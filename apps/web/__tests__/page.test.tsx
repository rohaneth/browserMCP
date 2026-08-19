import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import Page from '../app/page';

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    json: () => Promise.resolve({
      events: [
        {
          event_id: "1",
          timestamp: "2023-01-01T12:00:00Z",
          event_type: "page_loaded",
          domain: "example.com",
          page_title: "Example Title",
          source: "test"
        }
      ],
      total_count: 1,
      limit: 50,
      offset: 0
    })
  })
) as jest.Mock;

describe('Timeline Page', () => {
  it('renders loading state initially', () => {
    render(<Page />);
    expect(screen.getByTestId('loading-state')).toBeInTheDocument();
  });

  it('renders timeline list after fetch', async () => {
    render(<Page />);
    await waitFor(() => {
      expect(screen.getByTestId('timeline-list')).toBeInTheDocument();
      expect(screen.getByText(/Example Title/i)).toBeInTheDocument();
    });
  });
});
