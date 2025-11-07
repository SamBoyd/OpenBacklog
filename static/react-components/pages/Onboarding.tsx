import React from 'react';
import MCPSetupPage from '#components/onboarding/MCPSetupPage';
import AppBackground from '#components/AppBackground';
import NavBar from '#components/reusable/NavBar';

/**
 * Onboarding page with MCP setup instructions
 * Shows how to connect Claude Code and create first workspace/initiative
 */
const Onboarding: React.FC = () => {
  return (
    <AppBackground>
      <div className="inset-0 flex flex-col h-screen w-screen">
        <NavBar enableNavigation={false} />
        <div className='overflow-y-auto'>
          <MCPSetupPage />
        </div>
      </div>
    </AppBackground>
  )
};

export default Onboarding;