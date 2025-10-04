import { ErrorBoundary } from "react-error-boundary";
import { AppBackground } from "./AppBackground";
import NavBar from "./reusable/NavBar";
import { useNavigate } from "react-router";
import { ReactNode } from "react";
import * as Sentry from '@sentry/react';


export const ErrorFallback = ({ error, resetErrorBoundary }: { error: Error, resetErrorBoundary: () => void }): ReactNode => {
  const navigate = useNavigate();

  const handleReset = () => {
    resetErrorBoundary();
    navigate('/workspace/initiatives');
  }

  return (
    <AppBackground>
      <div className={`inset-0 flex flex-col h-screen w-screen`}>
        {/* Nav Bar */}
        <NavBar />

        <div className="relative w-full">
          <main className="grid min-h-full place-items-center px-6 py-24 sm:py-32 lg:px-8">
            <div className="text-center">
              <p className="text-base font-semibold text-primary">404</p>
              <h1 className="mt-4 text-balance text-5xl font-semibold tracking-tight text-foreground sm:text-7xl">
                Something went wrong.
              </h1>
              <p className="mt-6 text-pretty text-lg font-medium text-muted-foreground sm:text-xl/8">
                Sorry, that wasn't supposed to happen.
              </p>
              <div className="mt-10 flex items-center justify-center gap-x-6">
                <button
                  onClick={handleReset}
                  className={`
                    rounded-md bg-primary px-3.5 py-2.5 text-sm font-semibold text-foreground shadow-sm cursor-pointer
                    hover:bg-primary focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 
                    focus-visible:outline-primary
                    `}
                >
                  Go back home
                </button>
                <a href="#" className="text-sm font-semibold text-foreground">
                  Contact support <span aria-hidden="true">&rarr;</span>
                </a>
              </div>
            </div>
          </main>

        </div>
      </div>
    </AppBackground>
  )
};

const RootErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        // Log error to Sentry
        Sentry.captureException(error, {
          contexts: {
            react: {
              componentStack: errorInfo.componentStack,
            },
          },
        });
      }}
      onReset={(details) => {
        // Reset the state of your app so the error doesn't happen again
      }}
    >
      {children}
    </ErrorBoundary>
  );
};

export default RootErrorBoundary;