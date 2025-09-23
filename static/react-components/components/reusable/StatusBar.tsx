import React from 'react';
import { useUserPreferences } from '#hooks/useUserPreferences';
import Card from './Card';
import { Button } from './Button';

interface StatusBarProps {
    hidden?: boolean; // Optional prop to hide the status bar
}

const StatusBar = ({ hidden = false }: StatusBarProps) => {
    const { toggleTheme, preferences } = useUserPreferences();
    const [currentTime, setCurrentTime] = React.useState(new Date());

    // Update time every second
    React.useEffect(() => {
        const timer = setInterval(() => {
            setCurrentTime(new Date());
        }, 1000);

        return () => clearInterval(timer);
    }, []);

    const formattedTime = currentTime.toLocaleString('en-US', {
        weekday: 'short',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
    });

    // Conditionally render null if hidden is true
    if (hidden) {
        return null;
    }

    return (
        <Card
            className={
                `sticky bottom-0 right-0  h-8 flex items-center justify-between 
                 px-4 text-sm font-mono `}
        >
            {/* Left side */}
            <div className="flex items-center gap-2">
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    fill="currentColor"
                    className="size-4"
                >
                    <path fillRule="evenodd" d="M2.25 6a3 3 0 0 1 3-3h13.5a3 3 0 0 1 3 3v12a3 3 0 0 1-3 3H5.25a3 3 0 0 1-3-3V6Zm3.75 1.5a.75.75 0 0 0-.75.75v8.25c0 .414.336.75.75.75h13.5a.75.75 0 0 0 .75-.75V8.25a.75.75 0 0 0-.75-.75H6Z" clipRule="evenodd" />
                </svg>
                <span className=''>devtasks</span>
                <span className='text-muted-foreground'>:~$</span>
            </div>

            {/* Right side */}
            <div className="flex items-center gap-4">
                <Button
                    onClick={toggleTheme}
                    className='border-none'
                >
                    {preferences.theme === 'dark' ? (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="size-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
                        </svg>
                    )}
                </Button>
                <div className='flex items-end min-w-40'>
                    <span className='text-muted'>{formattedTime}</span>
                </div>
            </div>
        </Card>
    );
};

export default StatusBar;
