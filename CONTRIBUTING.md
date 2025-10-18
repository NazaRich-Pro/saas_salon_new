# Contributing to BeautyHub SaaS

Thank you for your interest in contributing to BeautyHub SaaS! This document provides guidelines and instructions for contributing.

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards other contributors

## How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in Issues
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Screenshots if applicable
   - Your environment (OS, browser, versions)

### Suggesting Features

1. Check if the feature has already been suggested
2. Open a new issue with:
   - Clear use case
   - Proposed solution
   - Alternative solutions considered
   - Any additional context

### Pull Requests

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/my-feature
   ```

3. **Make your changes**
   - Follow the code style guidelines
   - Add tests for new features
   - Update documentation as needed

4. **Test your changes**
   ```bash
   # Backend tests
   make test-api
   
   # Frontend tests
   make test-web
   
   # Linting
   make lint-api
   make lint-web
   ```

5. **Commit your changes**
   Follow conventional commits:
   ```bash
   git commit -m "feat: add new feature"
   git commit -m "fix: resolve bug in booking"
   git commit -m "docs: update API documentation"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/my-feature
   ```

7. **Open a Pull Request**
   - Provide a clear description
   - Reference any related issues
   - Include screenshots for UI changes
   - Ensure CI passes

## Development Setup

See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed setup instructions.

## Code Style

### Python (Django)

- Follow PEP 8
- Use Black for formatting (line length: 88)
- Use type hints where appropriate
- Write docstrings for functions and classes

Example:
```python
from typing import List, Optional

def get_available_slots(
    service_id: str,
    date: str,
    staff_id: Optional[str] = None
) -> List[dict]:
    """
    Get available booking slots for a service.
    
    Args:
        service_id: UUID of the service
        date: Date in YYYY-MM-DD format
        staff_id: Optional UUID of specific staff member
    
    Returns:
        List of available time slots
    """
    # Implementation
    pass
```

### TypeScript (Next.js)

- Use TypeScript for all new code
- Follow ESLint/Prettier configuration
- Use functional components with hooks
- Name components in PascalCase

Example:
```typescript
interface BookingFormProps {
  serviceId: string;
  onSubmit: (data: BookingData) => void;
}

export function BookingForm({ serviceId, onSubmit }: BookingFormProps) {
  // Implementation
}
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, semicolons, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Build process or auxiliary tool changes

Examples:
```bash
feat: add birthday campaign scheduler
fix: resolve double booking race condition
docs: update deployment guide
refactor: extract tenant resolution logic
test: add integration tests for payment flow
```

## Testing

### Backend (Python/Django)

```python
import pytest
from apps.booking.models import Appointment

@pytest.mark.django_db
def test_create_appointment():
    """Test appointment creation"""
    appointment = Appointment.objects.create(
        tenant_id="test-tenant",
        start_at="2025-10-15T10:00:00Z",
        end_at="2025-10-15T11:00:00Z",
    )
    assert appointment.status == 'PENDING'
```

### Frontend (TypeScript/React)

```typescript
import { render, screen } from '@testing-library/react';
import { BookingForm } from './BookingForm';

describe('BookingForm', () => {
  it('renders booking form', () => {
    render(<BookingForm serviceId="123" onSubmit={jest.fn()} />);
    expect(screen.getByText('Book Appointment')).toBeInTheDocument();
  });
});
```

## Documentation

- Update README.md for user-facing changes
- Update docs/ for technical changes
- Add JSDoc/docstrings for new functions
- Update API.md for API changes

## Review Process

1. All PRs require at least one review
2. CI must pass (linting, tests, build)
3. Documentation must be updated
4. Code coverage should not decrease

## Questions?

- Open a Discussion for general questions
- Join our community chat (if available)
- Contact maintainers via email

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.

Thank you for contributing! 🎉


