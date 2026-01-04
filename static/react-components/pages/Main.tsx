import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation, Outlet } from 'react-router';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { analytics } from '#services/analytics';
import * as Sentry from '@sentry/react';

import { UserPreferencesProvider, useUserPreferences } from '#hooks/useUserPreferences';
import { WorkspacesProvider } from '#hooks/useWorkspaces';
import { ActiveEntityProvider } from '#hooks/useActiveEntity';
import { SessionResetProvider } from '#hooks/SessionResetProvider';
import { InitiativesProvider } from '#contexts/InitiativesContext';
import { useIsDeviceMobile } from '#hooks/isDeviceMobile';
import { InitiativeGroupsProvider } from '#hooks/useInitiativeGroups';

import Initiatives from '#pages/Initiatives';
import Tasks from '#pages/Tasks';
import Onboarding from '#pages/Onboarding';
import Heroes from '#pages/Narrative/Heroes';
import Villains from '#pages/Narrative/Villains';
import Conflicts from '#pages/Narrative/Conflicts';
import RoadmapOverview from '#pages/RoadmapOverview';

import ViewInitiativeWrapper from '#components/ViewInitiativeWrapper';
import ViewTask from '#components/ViewTask';
import NavBar from '#components/reusable/NavBar';
import AppBackground from '#components/AppBackground';
import RootErrorBoundary from '#components/RootErrorBoundary';
import { TestError } from '#components/TestError';
import { ResponsiveLayout } from '#components/layout/ResponsiveLayout';
import AppGuard from '#components/onboarding/AppGuard';

import ContextDocument from './ContextDocument';
import { TasksProvider } from '#contexts/TasksContext';

import { GithubReposProvider } from '#hooks/useGithubRepos';
import StoryBiblePage from './Narrative/StoryBible';
import { RoadmapThemeDetail } from './Narrative/StoryArcDetail';
import StrategyFlowPage from './StrategyFlowPage';

import '../styles/output.css';


// Layout component for main app structure
const Layout: React.FC = () => {
    const isMobile = useIsDeviceMobile();

    return (
        <AppBackground>
            <div className="inset-0 flex flex-col h-screen w-screen">
                <NavBar />
                <ResponsiveLayout>
                    <Outlet />
                </ResponsiveLayout>
            </div>
        </AppBackground>
    );
};

export const MainContent = () => {
    return (
        <Routes>
            {/* Onboarding routes - not protected */}
            <Route path="/workspace/onboarding" element={<Onboarding />} />

            {/* Protected workspace routes */}
            <Route element={<AppGuard><Layout /></AppGuard>}>
                <Route path="/workspace/roadmap" element={<RoadmapOverview />} />
                <Route path="/workspace/strategy-flow" element={<StrategyFlowPage />} />
                <Route path="/workspace/story-bible" element={<StoryBiblePage />} />
                <Route path="/workspace/story-bible/theme/:themeId" element={<RoadmapThemeDetail />} />
                <Route path="/workspace/context" element={<ContextDocument />} />
                <Route path="/workspace/tasks" element={<Tasks />} />
                <Route path="/workspace/initiatives/:initiativeId/tasks/:taskId" element={<ViewTask />} />
                <Route path="/workspace/initiatives/:initiativeId" element={<ViewInitiativeWrapper />} />
                <Route path="/workspace/initiatives" element={<Initiatives />} />
                <Route path="/workspace/heroes" element={<Heroes />} />
                <Route path="/workspace/villains" element={<Villains />} />
                <Route path="/workspace/conflicts" element={<Conflicts />} />
                <Route path="/workspace" element={<Navigate to="/workspace/initiatives" />} />
            </Route>

            {/* Utility routes */}
            <Route path="/error" element={<TestError />} />
            <Route path="/" element={<Navigate to="/workspace/initiatives" />} />
            <Route path="*" element={<Navigate to="/workspace/initiatives" />} />
        </Routes>
    );
};

// Create a client
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: false,
            refetchOnWindowFocus: false,
        },
    },
});

const Main = () => {
    // Initialize analytics when the app starts
    useEffect(() => {
        analytics.initialize();
    }, []);

    return (
        <Sentry.ErrorBoundary fallback={<p>An error has occurred</p>}>
            <BrowserRouter>
                <RootErrorBoundary>
                    <SessionResetProvider>
                        <QueryClientProvider client={queryClient}>
                            <ActiveEntityProvider>
                                <UserPreferencesProvider>
                                    <WorkspacesProvider>
                                        <GithubReposProvider>
                                            <InitiativesProvider>
                                                <TasksProvider>
                                                    <InitiativeGroupsProvider>
                                                        <MainContent />
                                                    </InitiativeGroupsProvider>
                                                </TasksProvider>
                                            </InitiativesProvider>
                                        </GithubReposProvider>
                                    </WorkspacesProvider>
                                </UserPreferencesProvider>
                            </ActiveEntityProvider>
                        </QueryClientProvider>
                    </SessionResetProvider>
                </RootErrorBoundary>
            </BrowserRouter>
        </Sentry.ErrorBoundary>
    )
}

export default Main;
