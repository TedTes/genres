'use client';

import { useState, useEffect } from 'react';
import {JobsList,JobsFilter} from '../../components';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  type: string;
  description: string;
  requirements: string[];
  postedDate: string;
  category: string;
}

export default function JobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Fetch categories
    fetch('http://localhost:8000/api/jobs/categories')
      .then(response => response.json())
      .then(data => {
        setCategories(data);
      })
      .catch(err => {
        console.error('Error fetching categories:', err);
        setError('Failed to load job categories. Please try again later.');
      });
      
    // Fetch jobs (initially all jobs)
    fetchJobs();
  }, []);
  
  // Fetch jobs based on selected category
  const fetchJobs = (category?: string) => {
    setIsLoading(true);
    const url = category 
      ? `http://localhost:8000/api/jobs?category=${category}`
      : 'http://localhost:8000/api/jobs';
      
    fetch(url)
      .then(response => response.json())
      .then(data => {
        setJobs(data);
        setIsLoading(false);
      })
      .catch(err => {
        console.error('Error fetching jobs:', err);
        setError('Failed to load jobs. Please try again later.');
        setIsLoading(false);
      });
  };
  
  // Handle category selection
  const handleCategoryChange = (category: string) => {
    setSelectedCategory(category);
    fetchJobs(category || undefined);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Browse Jobs</h1>
      
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      
      <div className="flex flex-col md:flex-row gap-6">
        <div className="w-full md:w-1/4">
          <JobsFilter 
            categories={categories} 
            selectedCategory={selectedCategory}
            onCategoryChange={handleCategoryChange}
          />
        </div>
        
        <div className="w-full md:w-3/4">
          {isLoading ? (
            <div className="flex justify-center items-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
            </div>
          ) : (
            <JobsList jobs={jobs} />
          )}
        </div>
      </div>
    </div>
  );
}