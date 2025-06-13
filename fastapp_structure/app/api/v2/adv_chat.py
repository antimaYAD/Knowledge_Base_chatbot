from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from app.api.auth.auth import decode_token
from app.db.database import users_collection
from app.db.health_data_model import alert_collection,health_data_collection
from pydantic import BaseModel
from typing import List
from app.db.journal_model import journals_collection

from openai import OpenAI
# from langchain_community.llms import OpenAI
# from app.auth import get_current_user
import dateparser
from pydantic import BaseModel
from bson import ObjectId   
import os
from app.core.chatbot_engine import client
from app.core.advance_chatbot import *
from app.utils.optimized_code_rag import load_faiss_index, query_documents
from langchain_openai import ChatOpenAI, OpenAIEmbeddings  # ✅ For DeepSeek
from openai import OpenAI as OpenAIClient
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any, Optional
from app.db.database import conversations_collection
import json
from dotenv import load_dotenv
load_dotenv()
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class ChatRequest(BaseModel):
    question: str

class ChatResponse(BaseModel):
    reply: str




FAISS_FOLDER_PATH = os.path.join("data", "faiss_indexes")
client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL")
)
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL"),
    model=os.getenv("OPENAI_API_MODEL")
)

loaded_indexes= {}



@router.get("/metrics/heart_rate/summary")
def get_heart_rate_summary(token: str = Depends(oauth2_scheme)):
    valid, username = decode_token(token)
    if not valid:
        raise HTTPException(status_code=401, detail="Invalid token")

    entries = get_heart_rate_data(username)
    summary = summarize_heart_rate(entries)
    return {"reply": summary}

# # Route 2: Intelligent chat with personal + RAG logic

# def generate_mongo_query_nl_to_code(question: str, username: str):
#     """Convert natural language question to MongoDB query for your schema"""
#     system_prompt = (
#         "Convert user health questions to MongoDB query JSON. "
#         "Collection schema: {username: str, metric: str, timestamp: datetime, value: number, created_at: datetime}\n"
#         "Available metrics: 'steps', 'heartRate', 'spo2', 'blood_pressure'\n"
#         "Examples:\n"
#         "- 'my heart rate' → {\"metric\": \"heartRate\"}\n"
#         "- 'my steps today' → {\"metric\": \"steps\"}\n"
#         "- 'blood pressure data' → {\"metric\": \"blood_pressure\"}\n"
#         "Return ONLY the JSON object, no explanations."
#     )

#     try:
#         response = client.chat.completions.create(
#             model=os.getenv("OPENAI_API_MODEL"),
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": f"Question: {question}"}
#             ]
#         )

#         content = response.choices[0].message.content.strip()
#         print(f"🔁 GPT query generation: {content}")

#         import json
#         import re
        
#         # Extract JSON from response
#         json_match = re.search(r'\{.*\}', content, re.DOTALL)
#         if json_match:
#             json_str = json_match.group()
#             mongo_query = json.loads(json_str)
#             print(f"✅ Generated MongoDB query: {mongo_query}")
#             return mongo_query
            
#     except Exception as e:
#         print(f"❌ Query generation failed: {e}")
    
#     # Fallback: keyword-based query generation using your exact metric names
#     question_lower = question.lower()
#     if "heart rate" in question_lower or "heart" in question_lower:
#         return {"metric": "heartRate"}  # Match your schema
#     elif "steps" in question_lower or "walk" in question_lower:
#         return {"metric": "steps"}
#     elif "oxygen" in question_lower or "spo2" in question_lower:
#         return {"metric": "spo2"}
#     elif "blood pressure" in question_lower or "pressure" in question_lower:
#         return {"metric": "blood_pressure"}
#     else:
#         return {"metric": "heartRate"}  # default


# def execute_mongo_query(mongo_query: dict, username: str):
#     """Execute MongoDB query on your collections"""
#     try:
#         # Ensure security - always filter by username
#         mongo_query["username"] = username
#         print(f"🔍 Executing MongoDB query: {mongo_query}")
        
#         # Search in health_data_entries collection
#         result = list(health_data_collection.find(mongo_query))
#         print(f"📊 health_data_collection returned {len(result)} documents")

#         if not result:
#             # Try other collections if no health data found
#             try:
#                 journal_result = list(journals_collection.find({"username": username}))
#                 alert_result = list(alert_collection.find({"username": username}))
#                 result = journal_result + alert_result
#                 print(f"📊 Alternative collections returned {len(result)} documents")
#             except Exception as e:
#                 print(f"⚠️ Alternative collections not accessible: {e}")
        
#         return result
        
#     except Exception as e:
#         print(f"❌ MongoDB query execution failed: {e}")
#         return []


# def convert_mongo_results_to_natural_language(results: list, original_question: str, username: str):
#     """Convert MongoDB results to natural language answer using your schema"""
    
#     if not results:
#         return f"I couldn't find any {original_question.lower()} data in your health records."
    
#     # Prepare data summary for GPT using your schema fields
#     data_summary = []
    
#     for item in results:
#         if 'value' in item and 'metric' in item:
#             # Handle your timestamp format
#             timestamp = item.get('timestamp', item.get('created_at', 'Unknown time'))
#             metric_name = item['metric']
            
#             # Convert metric names to readable format
#             if metric_name == "heartRate":
#                 readable_metric = "Heart Rate"
#                 unit = "bpm"
#             elif metric_name == "steps":
#                 readable_metric = "Steps"
#                 unit = "steps"
#             elif metric_name == "spo2":
#                 readable_metric = "Blood Oxygen (SpO2)"
#                 unit = "%"
#             else:
#                 readable_metric = metric_name
#                 unit = ""
            
#             data_summary.append(f"{readable_metric}: {item['value']} {unit} at {timestamp}")
            
#         elif 'text' in item:  # Journal entry
#             data_summary.append(f"Journal: {item['text']}")
#         elif 'message' in item:  # Alert
#             data_summary.append(f"Alert: {item['message']}")
    
#     # Limit data to prevent token overflow
#     if len(data_summary) > 15:
#         data_summary = data_summary[:15]
#         data_summary.append("... and more entries")
    
#     data_text = "\n".join(data_summary)
    
#     system_prompt = (
#         f"You are a helpful health assistant. Convert the user's health data into a natural, informative response. "
#         f"Calculate averages, identify trends, and provide insights when appropriate. "
#         f"Be conversational and supportive. The user's name is {username}."
#     )
    
#     try:
#         response = client.chat.completions.create(
#             model=os.getenv("OPENAI_API_MODEL"),
#             messages=[
#                 {"role": "system", "content": system_prompt},
#                 {"role": "user", "content": f"Original question: {original_question}\n\nHealth data from database:\n{data_text}\n\nPlease provide a natural, helpful summary and answer to their question."}
#             ]
#         )
        
#         natural_answer = response.choices[0].message.content.strip()
#         print(f"✅ Generated natural language answer: {natural_answer[:100]}...")
#         return natural_answer
        
#     except Exception as e:
#         print(f"❌ Natural language conversion failed: {e}")
        
#         # Fallback: basic statistical summary using your schema
#         values = [r['value'] for r in results if 'value' in r and isinstance(r['value'], (int, float))]
#         if values:
#             avg = sum(values) / len(values)
#             min_val = min(values)
#             max_val = max(values)
#             metric = results[0].get('metric', 'data')
            
#             # Convert metric to readable name
#             if metric == "heartRate":
#                 metric_display = "heart rate (bpm)"
#             elif metric == "steps":
#                 metric_display = "steps"
#             elif metric == "spo2":
#                 metric_display = "blood oxygen (%)"
#             else:
#                 metric_display = metric
            
#             return (
#                 f"📊 **Your {metric_display} Summary:**\n\n"
#                 f"• **Average:** {avg:.1f}\n"
#                 f"• **Range:** {min_val} to {max_val}\n"
#                 f"• **Total entries:** {len(values)}\n\n"
#                 f"This data shows your recent {metric_display} trends. "
#                 f"{'Your levels look healthy!' if metric == 'heartRate' and 60 <= avg <= 100 else 'Keep tracking your progress!'}"
#             )
#         else:
#             return f"Found {len(results)} entries in your health records for {original_question}."


# # Updated main chat function for your collections
# @router.post("/chat/ask", response_model=ChatResponse)
# def ask_chatbot(req: ChatRequest, token: str = Depends(oauth2_scheme)):
#     valid, username = decode_token(token)
#     if not valid or not username:
#         raise HTTPException(status_code=401, detail="Invalid token or user not found")
    
#     query = normalize(req.question)
#     print(f"🎯 Processing question: {query}")
    
#     # For personal queries, use the complete MongoDB flow
#     if is_personal_query(query):
#         print("🔄 Personal query detected - using MongoDB flow")
        
#         # Step 1: Convert question to MongoDB query
#         mongo_query = generate_mongo_query_nl_to_code(query, username)
        
#         if mongo_query:
#             # Step 2: Execute the query
#             results = execute_mongo_query(mongo_query, username)
            
#             # Step 3: Convert results to natural language
#             if results:
#                 natural_answer = convert_mongo_results_to_natural_language(results, query, username)
#                 return {"reply": apply_personality(natural_answer, "friendly")}
#             else:
#                 return {"reply": apply_personality("I couldn't find any matching data in your health records. Try asking about your heart rate, steps, or other health metrics.", "friendly")}
    
#     # Fallback to knowledge base search for non-personal queries
#     print("🔄 Using knowledge base search for general health questions")
#     kb_matches = []
    
#     try:
#         for index_name in os.listdir(FAISS_FOLDER_PATH):
#             index_path = os.path.join(FAISS_FOLDER_PATH, index_name)
#             if os.path.isdir(index_path) and index_name.lower() != "gita":
#                 if index_name not in loaded_indexes:
#                     print(f"Loading index: {index_name}")
#                     loaded_indexes[index_name] = load_faiss_index(index_path)
                
#                 index = loaded_indexes[index_name]
#                 if index is not None:
#                     try:
#                         result_docs = index.as_retriever(search_kwargs={"k": 3}).invoke(query)
#                         kb_matches.extend([doc.page_content.strip() for doc in result_docs])
#                     except Exception as e:
#                         print(f"❌ Error querying index {index_name}: {e}")
#                         continue
#     except Exception as e:
#         print(f"❌ Knowledge base search failed: {e}")
    
#     if kb_matches:
#         best_answer = choose_best_answer(query, kb_matches)
#         return {"reply": apply_personality(best_answer, "friendly")}
    
#     return {"reply": apply_personality("⚠️ I couldn't find information to answer your question. Try asking about your personal health data or general health topics.", "friendly")}





# Route 3: "-------------------------------------------------------------------------------------"

# ===== INTELLIGENT QUERY ROUTER =====

def detect_query_type_and_context(question: str, username: str):
    """
    Intelligently detect if query needs personal data, general knowledge, or both
    Returns: query_type, data_sources, context_info
    """
    
    question_lower = question.lower()
    
    # Personal data indicators
    personal_indicators = [
        'my', 'mine', 'i', 'me', 'today', 'yesterday', 'last week', 'this week',
        'last month', 'this month', 'my data', 'my records', 'my journal',
        'my heart rate', 'my steps', 'my sleep', 'my calories'
    ]
    
    # Health metrics that could be personal
    health_metrics = [
        'heart rate', 'heartrate', 'pulse', 'bpm',
        'steps', 'walking', 'activity',
        'spo2', 'oxygen', 'blood oxygen',
        'sleep', 'sleeping', 'rest',
        'calories', 'calorie', 'energy',
        'blood pressure', 'pressure',
        'weight', 'bmi'
    ]
    
    # Context indicators (user wants to reference specific data)
    context_indicators = [
        'from', 'on', 'during', 'between', 'since', 'until',
        'june', 'july', 'monday', 'tuesday', 'yesterday', 'today',
        'last', 'previous', 'recent', 'latest'
    ]
    
    # General health question indicators
    general_indicators = [
        'what is', 'how does', 'why does', 'explain', 'tell me about',
        'definition', 'meaning', 'symptoms', 'causes', 'treatment',
        'normal range', 'healthy', 'should be', 'recommended'
    ]
    
    # Date extraction patterns
    date_patterns = [
        r'\d{1,2}\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{4}',
        r'\d{1,2}/\d{1,2}/\d{4}',
        r'\d{4}-\d{1,2}-\d{1,2}',
        r'today|yesterday|last week|this week'
    ]
    
    # Analyze the question
    has_personal = any(indicator in question_lower for indicator in personal_indicators)
    has_health_metric = any(metric in question_lower for metric in health_metrics)
    has_context = any(indicator in question_lower for indicator in context_indicators)
    has_general = any(indicator in question_lower for indicator in general_indicators)
    has_date = any(re.search(pattern, question_lower) for pattern in date_patterns)
    
    # Extract specific date if mentioned
    extracted_date = extract_date_from_question(question) if has_date else None
    
    # Extract specific metrics mentioned
    mentioned_metrics = [metric for metric in health_metrics if metric in question_lower]
    
    # Determine query type and data sources
    if has_personal and has_health_metric:
        if has_general:
            # Mixed query: "What's normal heart rate and what's my average?"
            query_type = "hybrid"
            data_sources = ["mongodb", "knowledge_base"]
        else:
            # Pure personal query: "What's my heart rate today?"
            query_type = "personal"
            data_sources = ["mongodb"]
    elif has_general and has_health_metric:
        if has_personal:
            # Hybrid: "Is my heart rate normal?" (needs both personal data and general knowledge)
            query_type = "hybrid"
            data_sources = ["mongodb", "knowledge_base"]
        else:
            # Pure general: "What is normal heart rate?"
            query_type = "general"
            data_sources = ["knowledge_base"]
    elif has_personal:
        # Personal query without specific health metric: "How am I doing today?"
        query_type = "personal"
        data_sources = ["mongodb"]
    else:
        # Default to general knowledge
        query_type = "general"
        data_sources = ["knowledge_base"]
    
    context_info = {
        "date": extracted_date,
        "metrics": mentioned_metrics,
        "has_context": has_context,
        "temporal_reference": has_date
    }
    
    print(f"🧠 Query Analysis: Type={query_type}, Sources={data_sources}, Context={context_info}")
    
    return query_type, data_sources, context_info


# ===== ENHANCED MONGODB QUERY GENERATOR =====

def generate_intelligent_mongo_query(question: str, username: str, context_info: Dict):
    """
    Generate MongoDB queries for any personal data request
    Supports health data, journal entries, alerts, and cross-collection queries
    """
    
    question_lower = question.lower()
    
    # Collection-specific query builders
    queries = {}
    
    # Health data queries
    health_metrics_map = {
        'heart rate': 'heartRate',
        'heartrate': 'heartRate',
        'pulse': 'heartRate',
        'bpm': 'heartRate',
        'steps': 'steps',
        'walking': 'steps',
        'activity': 'steps',
        'spo2': 'spo2',
        'oxygen': 'spo2',
        'blood oxygen': 'spo2',
        'sleep': 'sleep',
        'sleeping': 'sleep',
        'calories': 'calories',
        'calorie': 'calories',
        'blood pressure': 'blood_pressure',
        'pressure': 'blood_pressure'
    }
    
    # Build health data query if health metrics mentioned
    if context_info['metrics']:
        health_query = {"username": username}
        
        # Add specific metrics filter
        metric_filters = []
        for mentioned_metric in context_info['metrics']:
            if mentioned_metric in health_metrics_map:
                metric_filters.append(health_metrics_map[mentioned_metric])
        
        if metric_filters:
            if len(metric_filters) == 1:
                health_query["metric"] = metric_filters[0]
            else:
                health_query["metric"] = {"$in": metric_filters}
        
        # Add date filter if specified
        if context_info['date']:
            health_query["$or"] = [
                {"timestamp": {"$regex": f"^{context_info['date']}"}},
                {"created_at": {"$regex": f"^{context_info['date']}"}}
            ]
        
        queries["health_data"] = health_query
    
    # Journal queries (if user asks about feelings, mood, daily activities)
    journal_keywords = ['journal', 'diary', 'mood', 'feeling', 'day', 'personal', 'food', 'work', 'study']
    if any(keyword in question_lower for keyword in journal_keywords):
        journal_query = {"username": username}
        
        if context_info['date']:
            journal_query["timestamp"] = {"$regex": f"^{context_info['date']}"}
        
        queries["journal"] = journal_query
    
    # Alert queries (if user asks about notifications, warnings)
    alert_keywords = ['alert', 'notification', 'warning', 'reminder']
    if any(keyword in question_lower for keyword in alert_keywords):
        alert_query = {"username": username}
        
        if context_info['date']:
            alert_query["$or"] = [
                {"timestamp": {"$regex": f"^{context_info['date']}"}},
                {"created_at": {"$regex": f"^{context_info['date']}"}}
            ]
        
        queries["alerts"] = alert_query
    
    # If no specific collection detected but it's a personal query, search all
    if not queries and any(word in question_lower for word in ['my', 'i', 'me']):
        base_query = {"username": username}
        
        if context_info['date']:
            date_filter = {"$regex": f"^{context_info['date']}"}
            queries = {
                "health_data": {**base_query, "$or": [
                    {"timestamp": date_filter},
                    {"created_at": date_filter}
                ]},
                "journal": {**base_query, "timestamp": date_filter},
                "alerts": {**base_query, "$or": [
                    {"timestamp": date_filter},
                    {"created_at": date_filter}
                ]}
            }
        else:
            queries = {
                "health_data": base_query,
                "journal": base_query,
                "alerts": base_query
            }
    
    print(f"🔍 Generated MongoDB queries: {queries}")
    return queries


# ===== UNIFIED DATA FETCHER =====

def fetch_personal_data(queries: Dict, username: str) -> Dict[str, List]:
    """
    Execute multiple MongoDB queries and return organized results
    """
    
    results = {
        "health_data": [],
        "journal": [],
        "alerts": []
    }
    
    # Collection mapping
    collections = {
        "health_data": health_data_collection,
        "journal": journals_collection,
        "alerts": alert_collection
    }
    
    # Execute each query
    for query_type, query in queries.items():
        if query_type in collections:
            try:
                collection = collections[query_type]
                data = list(collection.find(query))
                results[query_type] = data
                print(f"📊 {query_type}: Found {len(data)} records")
            except Exception as e:
                print(f"❌ Error querying {query_type}: {e}")
                results[query_type] = []
    
    return results


# ===== INTELLIGENT CONTEXT BUILDER =====

def build_comprehensive_context(personal_data: Dict[str, List], question: str, username: str) -> str:
    """
    Build rich context from all personal data sources
    """
    
    context_parts = []
    
    # Process health data
    if personal_data["health_data"]:
        health_summary = process_health_data_for_context(personal_data["health_data"])
        if health_summary:
            context_parts.append(f"📊 **Health Data:**\n{health_summary}")
    
    # Process journal entries
    if personal_data["journal"]:
        journal_summary = process_journal_data_for_context(personal_data["journal"])
        if journal_summary:
            context_parts.append(f"📖 **Journal Entries:**\n{journal_summary}")
    
    # Process alerts
    if personal_data["alerts"]:
        alert_summary = process_alert_data_for_context(personal_data["alerts"])
        if alert_summary:
            context_parts.append(f"🚨 **Health Alerts:**\n{alert_summary}")
    
    return "\n\n".join(context_parts) if context_parts else ""


def process_health_data_for_context(health_data: List[Dict]) -> str:
    """Process health data into readable context - Fixed version"""
    
    if not health_data:
        return ""
    
    # Group by metric
    metrics = {}
    for item in health_data:
        metric = item.get('metric', 'unknown')
        if metric not in metrics:
            metrics[metric] = []
        
        value = item.get('value')
        timestamp_raw = item.get('timestamp', item.get('created_at', ''))
        
        # Handle timestamp properly
        if isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw.strftime("%Y-%m-%d %H:%M")
        elif isinstance(timestamp_raw, str):
            timestamp = timestamp_raw
        else:
            timestamp = str(timestamp_raw) if timestamp_raw else 'Unknown time'
        
        if value is not None:
            metrics[metric].append({
                'value': value,
                'timestamp': timestamp
            })
    
    # Create summaries for each metric
    summaries = []
    for metric, values in metrics.items():
        if values:
            # Calculate statistics
            numeric_values = [v['value'] for v in values if isinstance(v['value'], (int, float))]
            
            if numeric_values:
                avg = sum(numeric_values) / len(numeric_values)
                min_val = min(numeric_values)
                max_val = max(numeric_values)
                latest = values[-1]  # Most recent entry
                
                # Format metric name
                metric_display = {
                    'heartRate': 'Heart Rate (bpm)',
                    'steps': 'Steps',
                    'spo2': 'Blood Oxygen (%)',
                    'sleep': 'Sleep (hours)',
                    'calories': 'Calories',
                    'blood_pressure': 'Blood Pressure'
                }.get(metric, metric)
                
                summary = (
                    f"{metric_display}: Latest={latest['value']}, "
                    f"Average={avg:.1f}, Range={min_val}-{max_val} "
                    f"({len(values)} readings)"
                )
                summaries.append(summary)
    
    return "\n".join(summaries)

def process_journal_data_for_context(journal_data: List[Dict]) -> str:
    """Process journal data into readable context - Fixed version"""
    
    if not journal_data:
        return ""
    
    summaries = []
    for entry in journal_data:
        # Handle timestamp properly - it could be datetime object or string
        timestamp_raw = entry.get('timestamp', 'Unknown time')
        
        if isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw.strftime("%Y-%m-%d")
        elif isinstance(timestamp_raw, str):
            timestamp = timestamp_raw[:10] if len(timestamp_raw) >= 10 else timestamp_raw
        else:
            timestamp = str(timestamp_raw)[:10]
        
        mood = entry.get('mood', '')
        
        # Extract from response field
        if 'response' in entry:
            response_raw = entry['response']
            
            # Safe parsing using string operations
            try:
                if isinstance(response_raw, str):
                    # Extract values using string parsing
                    entry_parts = []
                    
                    # Extract food_intake
                    if 'food_intake' in response_raw:
                        food_match = re.search(r"'food_intake':\s*'([^']*)'", response_raw)
                        if food_match:
                            entry_parts.append(f"Food: {food_match.group(1)}")
                    
                    # Extract personal
                    if 'personal' in response_raw:
                        personal_match = re.search(r"'personal':\s*'([^']*)'", response_raw)
                        if personal_match:
                            entry_parts.append(f"Personal: {personal_match.group(1)}")
                    
                    # Extract work_or_study
                    if 'work_or_study' in response_raw:
                        work_match = re.search(r"'work_or_study':\s*'([^']*)'", response_raw)
                        if work_match:
                            entry_parts.append(f"Work: {work_match.group(1)}")
                    
                    # Extract sleep
                    if 'sleep' in response_raw:
                        sleep_match = re.search(r"'sleep':\s*'([^']*)'", response_raw)
                        if sleep_match:
                            entry_parts.append(f"Sleep: {sleep_match.group(1)}")
                    
                    # Extract extra_note
                    if 'extra_note' in response_raw:
                        note_match = re.search(r"'extra_note':\s*'([^']*)'", response_raw)
                        if note_match:
                            entry_parts.append(f"Notes: {note_match.group(1)}")
                    
                    if entry_parts:
                        summary = f"{timestamp} - {'; '.join(entry_parts)}"
                        if mood:
                            summary += f" (Mood: {mood})"
                        summaries.append(summary)
                    else:
                        # If no specific fields found, use the whole response
                        summary = f"{timestamp} - {response_raw}"
                        if mood:
                            summary += f" (Mood: {mood})"
                        summaries.append(summary)
                
            except Exception as e:
                print(f"⚠️ Error parsing journal response: {e}")
                # Ultimate fallback
                summary = f"{timestamp} - Journal entry available"
                if mood:
                    summary += f" (Mood: {mood})"
                summaries.append(summary)
        
        # Fallback to other text fields if response field doesn't exist
        elif 'text' in entry:
            summary = f"{timestamp} - {entry['text']}"
            if mood:
                summary += f" (Mood: {mood})"
            summaries.append(summary)
        else:
            # If no text content found
            summary = f"{timestamp} - Journal entry (no text content)"
            if mood:
                summary += f" (Mood: {mood})"
            summaries.append(summary)
    
    return "\n".join(summaries)

def process_alert_data_for_context(alert_data: List[Dict]) -> str:
    """Process alert data into readable context - Fixed version"""
    
    if not alert_data:
        return ""
    
    summaries = []
    for alert in alert_data:
        # Handle timestamp properly - it could be datetime object or string
        timestamp_raw = alert.get('timestamp', alert.get('created_at', 'Unknown time'))
        
        if isinstance(timestamp_raw, datetime):
            timestamp = timestamp_raw.strftime("%Y-%m-%d")
        elif isinstance(timestamp_raw, str):
            timestamp = timestamp_raw[:10] if len(timestamp_raw) >= 10 else timestamp_raw
        else:
            timestamp = str(timestamp_raw)[:10] if timestamp_raw else "Unknown time"
        
        message = alert.get('message', alert.get('text', 'No message'))
        priority = alert.get('priority', 'normal')
        
        summary = f"{timestamp} - [{priority.upper()}] {message}"
        summaries.append(summary)
    
    return "\n".join(summaries)


# ===== HYBRID RESPONSE GENERATOR =====

def generate_intelligent_response(question: str, personal_context: str, kb_context: List[str], 
                                query_type: str, username: str) -> str:
    """
    Generate intelligent response combining personal data and knowledge base
    """
    
    # Choose system prompt based on query type
    if query_type == "personal":
        system_prompt = (
            f"You are a personal health assistant for {username}. Answer their question using their personal health data. "
            f"Be specific, supportive, and provide actionable insights. Reference their actual data points and trends."
        )
        context_content = f"User's Personal Data:\n{personal_context}" if personal_context else "No personal data found."
        
    elif query_type == "general":
        system_prompt = (
            "You are a knowledgeable health assistant. Provide accurate, evidence-based health information. "
            "Be informative but remind users to consult healthcare professionals for medical advice."
        )
        context_content = f"Knowledge Base Information:\n{chr(10).join(kb_context)}" if kb_context else "Limited information available."
        
    elif query_type == "hybrid":
        system_prompt = (
            f"You are an intelligent health assistant for {username}. Answer their question by combining their personal data "
            f"with general health knowledge. Compare their data to normal ranges, identify patterns, and provide personalized insights."
        )
        
        context_parts = []
        if personal_context:
            context_parts.append(f"User's Personal Data:\n{personal_context}")
        if kb_context:
            context_parts.append(f"General Health Information:\n{chr(10).join(kb_context)}")
        
        context_content = "\n\n".join(context_parts) if context_parts else "Limited data available."
    
    else:
        # Fallback
        system_prompt = "You are a helpful health assistant. Answer the user's question to the best of your ability."
        context_content = personal_context or (chr(10).join(kb_context) if kb_context else "")
    
    # Generate response
    try:
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_API_MODEL"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {question}\n\nContext:\n{context_content}"}
            ]
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ Response generation failed: {e}")
        
        # Fallback response
        if personal_context:
            return f"Based on your personal data: {personal_context[:200]}..."
        elif kb_context:
            return f"General information: {kb_context[0][:200]}..."
        else:
            return "I couldn't find enough information to answer your question."


# ===== MAIN UNIFIED API =====
@router.post("/chat/ask", response_model=ChatResponse)
def ask_chatbot(req: ChatRequest, token: str = Depends(oauth2_scheme)):
    """
    Unified intelligent chatbot API that handles:
    - Personal health data queries (MongoDB)
    - General health questions (Knowledge Base)
    - Hybrid queries (Both sources)
    - Context-aware responses with date/metric filtering
    """

    valid, username = decode_token(token)
    if not valid or not username:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")

    query = normalize(req.question)
    print(f"🎯 Processing unified query: {query}")

    # Save user message
    save_message(username, "user", query)

    # Step 1: Analyze the query to determine type and context
    query_type, data_sources, context_info = detect_query_type_and_context(query, username)

    # Step 2: Fetch data from appropriate sources
    personal_context = ""
    kb_context = []

    # Fetch personal data if needed
    if "mongodb" in data_sources:
        print("🔄 Fetching personal data from MongoDB...")
        mongo_queries = generate_intelligent_mongo_query(query, username, context_info)

        if mongo_queries:
            personal_data = fetch_personal_data(mongo_queries, username)
            personal_context = build_comprehensive_context(personal_data, query, username)

    # Fetch knowledge base data if needed
    print("🔄 Searching knowledge base..plzzzz.")
    if "knowledge_base" in data_sources:
        print("🔄 Searching knowledge base...")
        try:
            for index_name in os.listdir(FAISS_FOLDER_PATH):
                index_path = os.path.join(FAISS_FOLDER_PATH, index_name)
                if os.path.isdir(index_path) and index_name.lower() != "gita":
                    if index_name not in loaded_indexes:
                        loaded_indexes[index_name] = load_faiss_index(index_path)

                    index = loaded_indexes[index_name]
                    if index is not None:
                        try:
                            result_docs = index.as_retriever(search_kwargs={"k": 3}).invoke(query)
                            kb_context.extend([doc.page_content.strip() for doc in result_docs])
                        except Exception as e:
                            print(f"❌ Error querying index {index_name}: {e}")
                            continue
        except Exception as e:
            print(f"❌ Knowledge base search failed: {e}")

    # Step 3: Generate intelligent response
    if personal_context or kb_context:
        response_text = generate_intelligent_response(
            query, personal_context, kb_context, query_type, username
        )
    else:
        response_text = "I couldn't find relevant information to answer your question. Try asking about your health data or general health topics."

    # Save assistant message
    save_message(username, "assistant", response_text)

    # Step 4: Apply personality and return
    final_response = apply_personality(response_text, "friendly")
    print(f"✅ Generated {query_type} response with {len(personal_context)} chars personal data and {len(kb_context)} KB sources")

    return {"reply": final_response}


def save_message(username, role, content):
    conversations_collection.update_one(
        {"username": username},
        {"$push": {"history": {"role": role, "content": content}}},
        upsert=True
    )

def get_recent_history(username, limit=6):
    doc = conversations_collection.find_one({"username": username})
    if doc:
        return doc.get("history", [])[-limit:]
    return []
