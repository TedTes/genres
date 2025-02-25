import React, { useState } from 'react';

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

interface JobCardProps {
  job: Job;
}

const JobCard: React.FC<JobCardProps> = ({ job }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  // Calculate days since posted
  const getDaysSincePosted = (dateString: string) => {
    const postedDate = new Date(dateString);
    const today = new Date();
    const diffTime = Math.abs(today.getTime() - postedDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const daysSincePosted = getDaysSincePosted(job.postedDate);
  
  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="p-5">
        <div className="flex justify-between">
          <h3 className="text-xl font-semibold text-gray-800">{job.title}</h3>
          <span className="inline-block px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded capitalize">
            {job.category}
          </span>
        </div>
        
        <div className="mt-2">
          <p className="text-gray-600">{job.company} • {job.location}</p>
          <p className="text-sm text-gray-500 mt-1">{job.type} • Posted {daysSincePosted} days ago</p>
        </div>
        
        <div className="mt-3">
          <p className="text-gray-700 line-clamp-2">
            {job.description}
          </p>
        </div>
        
        {isExpanded && (
          <div className="mt-4">
            <h4 className="font-medium text-gray-800 mb-2">Requirements</h4>
            <ul className="list-disc list-inside space-y-1 text-sm text-gray-600">
              {job.requirements.map((req, index) => (
                <li key={index}>{req}</li>
              ))}
            </ul>
            
            <div className="mt-5 flex space-x-3">
              <button className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded hover:bg-blue-700 transition-colors">
                Apply Now
              </button>
              <button className="px-4 py-2 border border-gray-300 text-gray-700 text-sm font-medium rounded hover:bg-gray-50 transition-colors">
                Match Resume
              </button>
            </div>
          </div>
        )}
        
        <button 
          className="mt-4 text-blue-600 text-sm font-medium flex items-center"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          {isExpanded ? 'Show Less' : 'Show More'}
          <svg 
            className={`ml-1 h-4 w-4 transform ${isExpanded ? 'rotate-180' : ''}`} 
            xmlns="http://www.w3.org/2000/svg" 
            viewBox="0 0 20 20" 
            fill="currentColor"
          >
            <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 011.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
    </div>
  );
};

export default JobCard;