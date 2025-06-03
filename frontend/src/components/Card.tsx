import React, { ReactNode } from 'react';

interface CardProps {
  title: string;
  value: string | number;
  icon?: ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ title, value, icon, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
        {icon && <div className="text-indigo-600">{icon}</div>}
      </div>
      <div className="text-3xl font-bold text-gray-900">{value}</div>
    </div>
  );
};

export default Card;