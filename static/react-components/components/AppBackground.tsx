import React, { useEffect, useRef } from "react";

export const AppBackground = ({ children }: { children: React.ReactNode }) => {
    const containerRef = useRef<HTMLDivElement>(null);

    // Add scroll tracking effect
    useEffect(() => {

        // Function to update the scroll offset CSS variable
        const updateScrollOffset = (event?: Event) => {
            if (!containerRef.current) {
                return;
            }

            // Determine the target element (either a specific scrollable element or window)
            const target = event?.target instanceof Element ? event.target : window;
            let scrollY = 0;

            if (target === window) {
                scrollY = window.scrollY;
            } else if ('scrollTop' in target) {
                scrollY = target.scrollTop;
            } else {
                return; // Don't update if we don't know the target
            }

            document.documentElement.style.setProperty('--scroll-offset', `${scrollY}px`);
        };

        // Initial call to set the offset
        updateScrollOffset();

        // Find and add scroll event listeners to all scrollable elements
        const scrollableElements = containerRef.current?.querySelectorAll('.overflow-y-auto') || [];

        scrollableElements.forEach((element, index) => {
            element.addEventListener('scroll', updateScrollOffset);
        });

        // Also listen to window scroll as fallback
        window.addEventListener('scroll', updateScrollOffset);

        // Clean up on unmount
        return () => {
            scrollableElements.forEach((element, index) => {
                element.removeEventListener('scroll', updateScrollOffset);
            });
            window.removeEventListener('scroll', updateScrollOffset);
        };
    }, []);

    return (
        <div ref={containerRef} className="relative flex-1 flex flex-row overflow-hidden bg-appbackground">
            {/* Animated gradient background with multiple radial gradients */}
            <div className="absolute inset-0 overflow-hidden">
                {/* First radial gradient - scrolls slower */}
                <div
                    className="absolute -top-[50vh] left-0 right-0 h-[300vh]"
                    style={{
                        background: 'radial-gradient(circle at 10% 40%, var(--appbackgroundgradient1) 0, transparent 20%)',
                        opacity: "var(--gradient-opacity)",
                        transform: "translateY(calc(var(--scroll-offset, 0) * 0.5))",
                    }}
                ></div>
                <div
                    className="absolute -top-[50vh] left-0 right-0 h-[300vh]"
                    style={{
                        background: 'radial-gradient(circle at 60% 40%, var(--appbackgroundgradient1) 0, transparent 20%)',
                        opacity: "var(--gradient-opacity)",
                        transform: "translateY(calc(var(--scroll-offset, 0) * 0.5))",
                    }}
                ></div>
                <div
                    className="absolute -top-[50vh] left-0 right-0 h-[300vh]"
                    style={{
                        background: 'radial-gradient(circle at 90% 40%, var(--appbackgroundgradient1) 0, transparent 20%)',
                        opacity: "var(--gradient-opacity)",
                        transform: "translateY(calc(var(--scroll-offset, 0) * 0.5))",
                    }}
                ></div>

                {/* Second radial gradient - scrolls slower */}
                <div
                    className="absolute -top-[50vh] left-0 right-0 h-[300vh]"
                    style={{
                        background: 'radial-gradient(circle at 80% 20%, var(--appbackgroundgradient2) 0, transparent 25%)',
                        opacity: "var(--gradient-opacity)",
                        transform: "translateY(calc(var(--scroll-offset, 0) * -0.5))",
                    }}
                ></div>
                

                {/* Third radial gradient - scrolls faster */}
                <div
                    className="absolute -top-[50vh] left-0 right-0 h-[300vh]"
                    style={{
                        background: 'radial-gradient(circle at 50% 50%, var(--appbackgroundgradient3) 0, transparent 20%)',
                        opacity: "var(--gradient-opacity)",
                        transform: "translateY(calc(var(--scroll-offset, 0) * -0.5))",
                    }}
                ></div>
            </div>

            {/* Content */}
            <div className="relative z-10 flex-1 flex flex-col">
                {children}
            </div>
        </div>
    );
};

export default AppBackground;
