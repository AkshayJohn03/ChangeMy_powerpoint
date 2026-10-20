import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

export interface CardProps extends HTMLMotionProps<'div'> {
  elevation?: 'none' | 'sm' | 'md' | 'lg';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className = '', elevation = 'sm', padding = 'md', children, ...props }, ref) => {
    
    const baseStyles = "bg-[var(--color-background-surface)] rounded-2xl border border-[var(--color-border-default)] overflow-hidden transition-all";
    
    const elevations = {
      none: "",
      sm: "shadow-sm",
      md: "shadow-md",
      lg: "shadow-lg"
    };

    const paddings = {
      none: "",
      sm: "p-4",
      md: "p-6",
      lg: "p-8"
    };

    return (
      <motion.div
        ref={ref}
        className={`${baseStyles} ${elevations[elevation]} ${paddings[padding]} ${className}`}
        {...props}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';
