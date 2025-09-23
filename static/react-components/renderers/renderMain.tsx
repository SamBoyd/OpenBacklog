import { createRoot } from 'react-dom/client';
import Main from '../pages/Main';
import { initializeAnalytics } from '#services/analytics';

initializeAnalytics();

if (document.getElementById('react-main')) {
  const container = document.getElementById('react-main')!;

  const root = createRoot(container);
  root.render(<Main />);
}