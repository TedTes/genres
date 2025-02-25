import Link from 'next/link';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-center text-center">
        <h1 className="text-4xl font-bold mb-8">ResumeMatcher</h1>
        <p className="text-xl mb-8">
          Find real-time job listings and automatically customize your resume to match job requirements
        </p>
        
        <div className="mt-10">
          <Link 
            href="/jobs"
            className="px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 transition-colors"
          >
            Browse Jobs
          </Link>
        </div>
      </div>
    </main>
  );
}