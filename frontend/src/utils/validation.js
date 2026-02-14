// Form Validation Utilities - ITEM 93: Validation helpers
export const validators = {
  required: (value) => {
    if (value === null || value === undefined || value === '') {
      return 'This field is required';
    }
    return null;
  },

  email: (value) => {
    if (!value) return null;
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) {
      return 'Invalid email address';
    }
    return null;
  },

  minLength: (min) => (value) => {
    if (!value) return null;
    if (value.length < min) {
      return `Must be at least ${min} characters`;
    }
    return null;
  },

  maxLength: (max) => (value) => {
    if (!value) return null;
    if (value.length > max) {
      return `Must be no more than ${max} characters`;
    }
    return null;
  },

  min: (min) => (value) => {
    if (value === null || value === undefined) return null;
    if (Number(value) < min) {
      return `Must be at least ${min}`;
    }
    return null;
  },

  max: (max) => (value) => {
    if (value === null || value === undefined) return null;
    if (Number(value) > max) {
      return `Must be no more than ${max}`;
    }
    return null;
  },

  pattern: (regex, message = 'Invalid format') => (value) => {
    if (!value) return null;
    if (!regex.test(value)) {
      return message;
    }
    return null;
  },

  url: (value) => {
    if (!value) return null;
    try {
      new URL(value);
      return null;
    } catch {
      return 'Invalid URL';
    }
  },

  phone: (value) => {
    if (!value) return null;
    const phoneRegex = /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/;
    if (!phoneRegex.test(value)) {
      return 'Invalid phone number';
    }
    return null;
  },

  password: (value) => {
    if (!value) return null;
    if (value.length < 8) {
      return 'Password must be at least 8 characters';
    }
    if (!/[a-z]/.test(value)) {
      return 'Password must contain at least one lowercase letter';
    }
    if (!/[A-Z]/.test(value)) {
      return 'Password must contain at least one uppercase letter';
    }
    if (!/[0-9]/.test(value)) {
      return 'Password must contain at least one number';
    }
    if (!/[!@#$%^&*]/.test(value)) {
      return 'Password must contain at least one special character (!@#$%^&*)';
    }
    return null;
  },

  confirmPassword: (passwordField) => (value, formData) => {
    if (!value) return null;
    if (value !== formData[passwordField]) {
      return 'Passwords do not match';
    }
    return null;
  },

  date: (value) => {
    if (!value) return null;
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    return null;
  },

  futureDate: (value) => {
    if (!value) return null;
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    if (date < new Date()) {
      return 'Date must be in the future';
    }
    return null;
  },

  pastDate: (value) => {
    if (!value) return null;
    const date = new Date(value);
    if (isNaN(date.getTime())) {
      return 'Invalid date';
    }
    if (date > new Date()) {
      return 'Date must be in the past';
    }
    return null;
  },
};

// Combine multiple validators
export const combine = (...validatorFns) => (value, formData) => {
  for (const validator of validatorFns) {
    const error = validator(value, formData);
    if (error) return error;
  }
  return null;
};

// Validate an entire form
export const validateForm = (formData, rules) => {
  const errors = {};
  let isValid = true;

  for (const field in rules) {
    const fieldRules = Array.isArray(rules[field]) ? rules[field] : [rules[field]];
    const value = formData[field];

    for (const rule of fieldRules) {
      const error = rule(value, formData);
      if (error) {
        errors[field] = error;
        isValid = false;
        break; // Stop at first error for this field
      }
    }
  }

  return { isValid, errors };
};

export default validators;
