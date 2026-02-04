import React from 'react';
import ScheduleUpload from '../components/ScheduleUpload.jsx';

/**
 * SchedulePage presents the schedule analysis tool.  It explains what
 * formats are supported and wraps the ScheduleUpload component.
 */
export default function SchedulePage() {
  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Schedule Analysis</h1>
      <p className="mb-4 text-gray-700">
        Upload a Primavera XER or Microsoft Project XML/MPP file to compute
        tasks, critical path and overall project duration. Results will be
        returned asynchronously and displayed below.
      </p>
      <ScheduleUpload />
    </div>
  );
}