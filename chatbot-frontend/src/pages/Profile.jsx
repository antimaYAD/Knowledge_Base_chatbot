import React, { useState, useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import {
  update,
  clearError,
  clearSuccessFlags,
} from "../features/auth/authSlice";
import {
  selectAuthLoading,
  selectAuthError,
  selectUpdateSuccess,
} from "../features/auth/authSelectors";

const Profile = () => {
  const dispatch = useDispatch();
  const isLoading = useSelector(selectAuthLoading);
  const error = useSelector(selectAuthError);
  const updateSuccess = useSelector(selectUpdateSuccess);

  const [formData, setFormData] = useState({
    email: "",
    age: "",
    gender: "",
  });

  const [successMessage, setSuccessMessage] = useState("");

  // Show success message when update is successful
  useEffect(() => {
    if (updateSuccess) {
      setSuccessMessage("Profile updated successfully");

      // Clear success message after 3 seconds
      const timer = setTimeout(() => {
        setSuccessMessage("");
        dispatch(clearSuccessFlags());
      }, 3000);

      return () => clearTimeout(timer);
    }

    // Clear errors and success flags when unmounting
    return () => {
      dispatch(clearError());
      dispatch(clearSuccessFlags());
    };
  }, [updateSuccess, dispatch]);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    // Filter out empty fields and convert age to number if provided
    const updateData = Object.entries(formData).reduce((acc, [key, value]) => {
      if (value !== "") {
        if (key === "age") {
          acc[key] = parseInt(value);
        } else {
          acc[key] = value;
        }
      }
      return acc;
    }, {});

    if (Object.keys(updateData).length > 0) {
      dispatch(update(updateData));
    }
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="px-4 py-5 sm:px-6">
        <h3 className="text-lg leading-6 font-medium text-gray-900">
          User Profile
        </h3>
        <p className="mt-1 max-w-2xl text-sm text-gray-500">
          Update your personal information.
        </p>
      </div>

      <div className="border-t border-gray-200 px-4 py-5 sm:p-6">
        {successMessage && (
          <div className="rounded-md bg-green-50 p-4 mb-4">
            <div className="flex">
              <div className="ml-3">
                <p className="text-sm font-medium text-green-800">
                  {successMessage}
                </p>
              </div>
            </div>
          </div>
        )}

        {error && (
          <div className="rounded-md bg-red-50 p-4 mb-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">{error}</h3>
              </div>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="email"
              className="block text-sm font-medium text-gray-700"
            >
              Email
            </label>
            <div className="mt-1">
              <input
                id="email"
                name="email"
                type="email"
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Your email address"
                value={formData.email}
                onChange={handleChange}
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Leave empty if you don't want to change.
            </p>
          </div>

          <div>
            <label
              htmlFor="age"
              className="block text-sm font-medium text-gray-700"
            >
              Age
            </label>
            <div className="mt-1">
              <input
                id="age"
                name="age"
                type="number"
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                placeholder="Your age"
                value={formData.age}
                onChange={handleChange}
              />
            </div>
          </div>

          <div>
            <label
              htmlFor="gender"
              className="block text-sm font-medium text-gray-700"
            >
              Gender
            </label>
            <div className="mt-1">
              <select
                id="gender"
                name="gender"
                className="shadow-sm focus:ring-indigo-500 focus:border-indigo-500 block w-full sm:text-sm border-gray-300 rounded-md"
                value={formData.gender}
                onChange={handleChange}
              >
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
            >
              {isLoading ? "Updating..." : "Update Profile"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Profile;
