import React from 'react';

interface JobsFilterProps {
  categories: string[];
  selectedCategory: string;
  onCategoryChange: (category: string) => void;
}

const JobsFilter: React.FC<JobsFilterProps> = ({ 
  categories, 
  selectedCategory, 
  onCategoryChange 
}) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h2 className="text-lg font-semibold mb-4">Filter Jobs</h2>
      
      <div className="mb-4">
        <h3 className="text-sm font-medium mb-2">Categories</h3>
        <div className="space-y-2">
          <div className="flex items-center">
            <input
              id="all-categories"
              type="radio"
              name="category"
              checked={selectedCategory === ''}
              onChange={() => onCategoryChange('')}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500"
            />
            <label htmlFor="all-categories" className="ml-2 text-sm text-gray-700 capitalize">
              All Categories
            </label>
          </div>
          
          {categories.map((category) => (
            <div key={category} className="flex items-center">
              <input
                id={`category-${category}`}
                type="radio"
                name="category"
                checked={selectedCategory === category}
                onChange={() => onCategoryChange(category)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500"
              />
              <label htmlFor={`category-${category}`} className="ml-2 text-sm text-gray-700 capitalize">
                {category}
              </label>
            </div>
          ))}
        </div>
      </div>
      
      {/* ????? add more filters here */}
      {/* 
      <div className="mb-4">
        <h3 className="text-sm font-medium mb-2">Job Type</h3>
        // Job type filters
      </div>
      
      <div className="mb-4">
        <h3 className="text-sm font-medium mb-2">Location</h3>
        // Location filters
      </div>
      */}
    </div>
  );
};

export default JobsFilter;