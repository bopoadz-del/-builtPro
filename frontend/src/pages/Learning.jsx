import React, { useState, useEffect } from 'react';
import { BookOpen, Video, FileText, Award, TrendingUp, Clock, CheckCircle, Play, Lock } from 'lucide-react';

const Learning = () => {
  const [courses, setCourses] = useState([]);
  const [activeTab, setActiveTab] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCourses();
  }, [activeTab]);

  const fetchCourses = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (activeTab !== 'all') params.append('filter', activeTab);

      const response = await fetch(`/api/v1/learning/courses?${params}`);
      const data = await response.json();
      setCourses(data.items || []);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      // Mock data for demo
      setCourses([
        {
          id: 1,
          title: 'BIM Fundamentals',
          description: 'Learn the basics of Building Information Modeling',
          type: 'video',
          duration: '4h 30m',
          progress: 65,
          lessons: 12,
          completed: 8,
          level: 'Beginner',
          instructor: 'John Smith',
          thumbnail: 'https://via.placeholder.com/300x200',
        },
        {
          id: 2,
          title: 'Advanced IFC Parsing',
          description: 'Deep dive into IFC file structures and parsing',
          type: 'interactive',
          duration: '6h 15m',
          progress: 0,
          lessons: 18,
          completed: 0,
          level: 'Advanced',
          instructor: 'Sarah Johnson',
          thumbnail: 'https://via.placeholder.com/300x200',
        },
        {
          id: 3,
          title: 'Construction Economics 101',
          description: 'Understanding cost estimation and budgeting',
          type: 'video',
          duration: '3h 20m',
          progress: 100,
          lessons: 10,
          completed: 10,
          level: 'Intermediate',
          instructor: 'Mike Davis',
          thumbnail: 'https://via.placeholder.com/300x200',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const tabs = [
    { id: 'all', label: 'All Courses', icon: BookOpen },
    { id: 'in-progress', label: 'In Progress', icon: TrendingUp },
    { id: 'completed', label: 'Completed', icon: CheckCircle },
  ];

  const getProgressColor = (progress) => {
    if (progress === 0) return 'bg-gray-200 dark:bg-gray-700';
    if (progress < 50) return 'bg-yellow-500';
    if (progress < 100) return 'bg-blue-500';
    return 'bg-green-500';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Learning Center</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Expand your knowledge with interactive courses and tutorials
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
          <Award className="w-5 h-5" />
          My Certificates
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Courses</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {courses.length}
              </p>
            </div>
            <BookOpen className="w-8 h-8 text-blue-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">In Progress</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {courses.filter(c => c.progress > 0 && c.progress < 100).length}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-yellow-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Completed</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                {courses.filter(c => c.progress === 100).length}
              </p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Total Hours</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-1">
                24h
              </p>
            </div>
            <Clock className="w-8 h-8 text-purple-600" />
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="flex -mb-px">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-6 py-4 border-b-2 font-medium text-sm transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                      : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Courses Grid */}
        <div className="p-6">
          {loading ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              Loading courses...
            </div>
          ) : courses.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              No courses found
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {courses.map((course) => (
                <div
                  key={course.id}
                  className="bg-white dark:bg-gray-700 rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow"
                >
                  {/* Thumbnail */}
                  <div className="relative h-48 bg-gradient-to-br from-blue-500 to-purple-600">
                    <div className="absolute inset-0 flex items-center justify-center">
                      {course.progress > 0 ? (
                        <Play className="w-16 h-16 text-white opacity-80" />
                      ) : (
                        <Lock className="w-16 h-16 text-white opacity-80" />
                      )}
                    </div>
                    <div className="absolute top-2 right-2">
                      <span className="px-2 py-1 bg-white/90 text-xs font-semibold rounded">
                        {course.level}
                      </span>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="p-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                      {course.title}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                      {course.description}
                    </p>

                    {/* Progress Bar */}
                    {course.progress > 0 && (
                      <div className="mb-4">
                        <div className="flex justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                          <span>{course.progress}% Complete</span>
                          <span>{course.completed}/{course.lessons} lessons</span>
                        </div>
                        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all ${getProgressColor(course.progress)}`}
                            style={{ width: `${course.progress}%` }}
                          />
                        </div>
                      </div>
                    )}

                    {/* Meta Info */}
                    <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400 mb-4">
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {course.duration}
                      </div>
                      <div className="flex items-center gap-1">
                        <FileText className="w-4 h-4" />
                        {course.lessons} lessons
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">
                        {course.instructor}
                      </span>
                      <button className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors">
                        {course.progress === 0 ? 'Start' : course.progress === 100 ? 'Review' : 'Continue'}
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Recommended Learning Paths */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow">
        <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
          Recommended Learning Paths
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 transition-colors cursor-pointer">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              BIM Specialist Track
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Master BIM fundamentals, IFC parsing, and 3D modeling
            </p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">5 courses • 20 hours</span>
              <span className="text-sm text-blue-600 dark:text-blue-400 font-medium">View Path →</span>
            </div>
          </div>

          <div className="p-4 border border-gray-200 dark:border-gray-700 rounded-lg hover:border-blue-500 transition-colors cursor-pointer">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-2">
              Construction Economics
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
              Learn cost estimation, budgeting, and financial analysis
            </p>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">4 courses • 16 hours</span>
              <span className="text-sm text-blue-600 dark:text-blue-400 font-medium">View Path →</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Learning;
