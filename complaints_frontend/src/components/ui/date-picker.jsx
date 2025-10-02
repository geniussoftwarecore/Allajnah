import React from 'react';
import { Button } from './button';
import { Calendar } from 'lucide-react';

// Simple date picker placeholder component
export const DatePickerWithRange = ({ className, ...props }) => {
  return (
    <Button variant="outline" className={className} {...props}>
      <Calendar className="mr-2 h-4 w-4" />
      اختر التاريخ
    </Button>
  );
};

export default DatePickerWithRange;
