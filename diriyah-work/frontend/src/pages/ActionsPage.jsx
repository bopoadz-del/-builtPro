import React from 'react';
import ActionItemsManager from '../components/ActionItemsManager';

export default function ActionsPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-6xl">
        <ActionItemsManager projectId="heritage-quarter" />
      </div>
    </div>
  );
}
