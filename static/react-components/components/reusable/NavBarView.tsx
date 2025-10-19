import React from 'react';
import { MdBento, MdCategory, MdMenu, MdClose } from 'react-icons/md';
import { FaChartLine, FaDatabase } from "react-icons/fa6";
import { ButtonProps, NoBorderButton } from './Button';

const NAV_BAR_ICON_SIZE = 'size-5';

const NavBarButton = ({ icon, title, onClick, active }: { icon: React.ReactNode, title: string, onClick: () => void, active: boolean }) => {
    return (
        <button
            title={title}
            onClick={onClick}
            className={
                `
         rounded
         flex items-center justify-center
         gap-x-1.5 px-2.5 py-1.5
         ${active ? 'text-sidebar-foreground' : 'text-sidebar-foreground/80'}
         ${active ? 'cursor-default' : ''}
         hover:text-sidebar-foreground
         `
            }
        >
            {icon}
            <span>{title}</span>
        </button>
    );
};

export const MobileNavBarButton: React.FC<ButtonProps> = ({ useRef, id, title, onClick, className, dataTestId, disabled, icon, active }) => {
    return (
        <button
            ref={useRef}
            id={id}
            title={title}
            onClick={onClick}
            className={
                `${className}
             flex items-center justify-start
             gap-x-1.5 px-2.5 py-1.5
             ${active ? 'bg-primary text-primary-foreground' : 'text-sidebar-foreground hover:bg-primary/15 hover:text-primary-foreground'}
             `
            }
            disabled={disabled}
            data-testid={dataTestId}
        >
            {icon}
            <span>{title}</span>
        </button>
    );
};

interface NavBarViewProps {
    enableNavigation: boolean;
    isMenuOpen: boolean;
    currentPath: string;
    onToggleMenu: () => void;
    onNavigate: (path: string) => void;
    backlogPath: string;
    dashboardPath: string;
    initiativesPath: string;
    tasksPath: string;
    supportPath: string;
    accountPath: string;
    billingPath: string;
    strategyPath: string;
    toggleTheme: () => void;
    currentTheme: string;
}

const NavBarView: React.FC<NavBarViewProps> = ({
    enableNavigation,
    isMenuOpen,
    currentPath,
    onToggleMenu,
    onNavigate,
    currentTheme,
    toggleTheme,
    backlogPath,
    initiativesPath,
    tasksPath,
    supportPath,
    accountPath,
    billingPath,
    strategyPath,
}) => {
    return (
        <nav className="top-0 left-0 right-0 bg-sidebar text-sidebar-foreground h-18 grow-0 flex flex-col justify-center relative z-20"> {/* Increased z-index for navbar */}
            <div className="w-full mx-auto ">
                <div className="flex justify-between items-center h-12 px-3"> {/* Ensure items are centered vertically */}
                    <div className="flex items-center space-x-2"> {/* Group Logo and Switcher */}
                        <span className="tracking-wide text-sidebar-foreground/80 cursor-default">OpenBacklog</span>
                    </div>

                    {enableNavigation && (
                        <>
                            {/* Mobile Menu Button */}
                            <div className="md:hidden">
                                <button
                                    onClick={onToggleMenu}
                                    className="inline-flex items-center justify-center p-2 rounded-md text-sidebar-foreground hover:text-primary hover:bg-muted/5 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary"
                                    aria-controls="mobile-menu"
                                    aria-expanded={isMenuOpen}
                                >
                                    <span className="sr-only">Open main menu</span>
                                    {isMenuOpen ? (
                                        <MdClose className="block h-6 w-6" aria-hidden="true" />
                                    ) : (
                                        <MdMenu className="block h-6 w-6" aria-hidden="true" />
                                    )}
                                </button>
                            </div>

                            {/* Desktop Action Icons */}
                            <div data-testid="nav-bar-actions" className="pr-2 hidden md:flex items-center text-sidebar-foreground gap-0.5"> {/* Reduced gap for desktop */}
                                {/* Desktop Menu Items */}
                                <div className="hidden md:flex md:items-center md:flex-grow md:justify-start pl-20 md:ml-6"> {/* Adjusted for desktop */}
                                    {/* Breadcrumb/Nav Links */}
                                    <div className="flex items-center space-x-2">
                                        <NavBarButton
                                            icon={<FaDatabase size="0.8em" />}
                                            title="Backlog"
                                            onClick={() => onNavigate(backlogPath)}
                                            active={currentPath.includes(backlogPath)}
                                        />
                                        <NavBarButton
                                            icon={<MdBento />}
                                            title="Initiatives"
                                            onClick={() => onNavigate(initiativesPath)}
                                            active={currentPath.includes(initiativesPath)}
                                        />
                                        <NavBarButton
                                            icon={<MdCategory />}
                                            title="Tasks"
                                            onClick={() => onNavigate(tasksPath)}
                                            active={currentPath.includes(tasksPath)}
                                        />
                                        <NavBarButton
                                            icon={<FaChartLine />}
                                            title="Strategy"
                                            onClick={() => onNavigate(strategyPath)}
                                            active={currentPath.includes(strategyPath)}
                                            />
                                    </div>
                                </div>

                                {/* TODO - reintroduce once spacing theme is implemented */}
                                {/* <CompactSelector /> */}

                                <NoBorderButton
                                    onClick={toggleTheme}
                                    className='text-sidebar-foreground/80 hover:text-sidebar-foreground rounded-md p-1.5'
                                >
                                    {currentTheme === 'dark' ? (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.72 9.72 0 0 1 18 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 0 0 3 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 0 0 9.002-5.998Z" />
                                        </svg>
                                    ) : (
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386-1.591 1.591M21 12h-2.25m-.386 6.364-1.591-1.591M12 18.75V21m-4.773-4.227-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0Z" />
                                        </svg>
                                    )}
                                </NoBorderButton>

                                <NoBorderButton
                                    onClick={() => window.location.assign(supportPath)}
                                    className='text-sidebar-foreground/80 hover:text-sidebar-foreground rounded-md p-1.5'
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.712 4.33a9.027 9.027 0 0 1 1.652 1.306c.51.51.944 1.064 1.306 1.652M16.712 4.33l-3.448 4.138m3.448-4.138a9.014 9.014 0 0 0-9.424 0M19.67 7.288l-4.138 3.448m4.138-3.448a9.014 9.014 0 0 1 0 9.424m-4.138-5.976a3.736 3.736 0 0 0-.88-1.388 3.737 3.737 0 0 0-1.388-.88m2.268 2.268a3.765 3.765 0 0 1 0 2.528m-2.268-4.796a3.765 3.765 0 0 0-2.528 0m4.796 4.796c-.181.506-.475.982-.88 1.388a3.736 3.736 0 0 1-1.388.88m2.268-2.268 4.138 3.448m0 0a9.027 9.027 0 0 1-1.306 1.652c-.51.51-1.064.944-1.652 1.306m0 0-3.448-4.138m3.448 4.138a9.014 9.014 0 0 1-9.424 0m5.976-4.138a3.765 3.765 0 0 1-2.528 0m0 0a3.736 3.736 0 0 1-1.388-.88 3.737 3.737 0 0 1-.88-1.388m2.268 2.268L7.288 19.67m0 0a9.024 9.024 0 0 1-1.652-1.306 9.027 9.027 0 0 1-1.306-1.652m0 0 4.138-3.448M4.33 16.712a9.014 9.014 0 0 1 0-9.424m4.138 5.976a3.765 3.765 0 0 1 0-2.528m0 0c.181-.506.475-.982.88-1.388a3.736 3.736 0 0 1 1.388-.88m-2.268 2.268L4.33 7.288m6.406 1.18L7.288 4.33m0 0a9.024 9.024 0 0 0-1.652 1.306A9.025 9.025 0 0 0 4.33 7.288" />
                                    </svg>
                                </NoBorderButton>

                                <NoBorderButton
                                    onClick={() => onNavigate(billingPath)}
                                    className='text-sidebar-foreground/80 hover:text-sidebar-foreground rounded-md p-1.5'
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" />
                                    </svg>
                                </NoBorderButton>

                                <NoBorderButton
                                    onClick={() => window.location.assign(accountPath)}
                                    className='text-sidebar-foreground/80 hover:text-sidebar-foreground rounded-md p-1.5'
                                >
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 0 1 1.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.559.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.894.149c-.424.07-.764.383-.929.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 0 1-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.398.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 0 1-.12-1.45l.527-.737c.25-.35.272-.806.108-1.204-.165-.397-.506-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.108-1.204l-.526-.738a1.125 1.125 0 0 1 .12-1.45l.773-.773a1.125 1.125 0 0 1 1.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894Z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                                    </svg>
                                </NoBorderButton>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {enableNavigation && (
                <>
                    {/* Mobile Menu, show/hide based on menu state */}
                    <div className={`${isMenuOpen ? 'block' : 'hidden'} md:hidden max-w-sm absolute top-12 right-0  bg-sidebar shadow-md z-10`} id="mobile-menu">
                        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                            <MobileNavBarButton
                                icon={<FaDatabase size="0.8em" />}
                                title="Backlog"
                                onClick={() => onNavigate(backlogPath)}
                                active={currentPath.includes(backlogPath)}
                                className="block w-full text-left"
                            >
                                <span>Backlog</span>
                            </MobileNavBarButton>
                            <MobileNavBarButton
                                icon={<MdBento />}
                                title="Initiatives"
                                onClick={() => onNavigate(initiativesPath)}
                                active={currentPath.includes(initiativesPath)}
                                className="block w-full text-left"
                            >
                                <span>Initiatives</span>
                            </MobileNavBarButton>
                            <MobileNavBarButton
                                icon={<MdCategory />}
                                title="Tasks"
                                onClick={() => onNavigate(tasksPath)}
                                active={currentPath.includes(tasksPath)}
                                className="block w-full text-left"
                            >
                                <span>Tasks</span>
                            </MobileNavBarButton>
                            <MobileNavBarButton
                                icon={<FaChartLine />}
                                title="Strategy"
                                onClick={() => onNavigate(strategyPath)}
                                active={currentPath.includes(strategyPath)}
                                className="block w-full text-left"
                            >
                                <span>Strategy</span>
                            </MobileNavBarButton>
                        </div>
                        {/* Mobile Action Icons */}
                        <div className="pt-4 pb-3 border-t border-border">
                            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
                                <a href={supportPath} onClick={onToggleMenu} className="flex items-center gap-2 text-sidebar-foreground hover:text-primary rounded-md p-2 w-full">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.712 4.33a9.027 9.027 0 0 1 1.652 1.306c.51.51.944 1.064 1.306 1.652M16.712 4.33l-3.448 4.138m3.448-4.138a9.014 9.014 0 0 0-9.424 0M19.67 7.288l-4.138 3.448m4.138-3.448a9.014 9.014 0 0 1 0 9.424m-4.138-5.976a3.736 3.736 0 0 0-.88-1.388 3.737 3.737 0 0 0-1.388-.88m2.268 2.268a3.765 3.765 0 0 1 0 2.528m-2.268-4.796a3.765 3.765 0 0 0-2.528 0m4.796 4.796c-.181.506-.475.982-.88 1.388a3.736 3.736 0 0 1-1.388.88m2.268-2.268 4.138 3.448m0 0a9.027 9.027 0 0 1-1.306 1.652c-.51.51-1.064.944-1.652 1.306m0 0-3.448-4.138m3.448 4.138a9.014 9.014 0 0 1-9.424 0m5.976-4.138a3.765 3.765 0 0 1-2.528 0m0 0a3.736 3.736 0 0 1-1.388-.88 3.737 3.737 0 0 1-.88-1.388m2.268 2.268L7.288 19.67m0 0a9.024 9.024 0 0 1-1.652-1.306 9.027 9.027 0 0 1-1.306-1.652m0 0 4.138-3.448M4.33 16.712a9.014 9.014 0 0 1 0-9.424m4.138 5.976a3.765 3.765 0 0 1 0-2.528m0 0c.181-.506.475-.982.88-1.388a3.736 3.736 0 0 1 1.388-.88m-2.268 2.268L4.33 7.288m6.406 1.18L7.288 4.33m0 0a9.024 9.024 0 0 0-1.652 1.306A9.025 9.025 0 0 0 4.33 7.288" />
                                    </svg>
                                    <span>Support</span>
                                </a>
                                <div onClick={() => onNavigate(billingPath)} className="flex items-center gap-2 text-sidebar-foreground hover:text-primary rounded-md p-2 w-full cursor-pointer">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 8.25h19.5M2.25 9h19.5m-16.5 5.25h6m-6 2.25h3m-3.75 3h15a2.25 2.25 0 0 0 2.25-2.25V6.75A2.25 2.25 0 0 0 19.5 4.5h-15a2.25 2.25 0 0 0-2.25 2.25v10.5A2.25 2.25 0 0 0 4.5 19.5Z" />
                                    </svg>
                                    <span>Billing</span>
                                </div>
                                <a href={accountPath} onClick={onToggleMenu} className="flex items-center gap-2 text-sidebar-foreground hover:text-primary rounded-md p-2 w-full">
                                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" className={NAV_BAR_ICON_SIZE}>
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93.398.164.855.142 1.205-.108l.737-.527a1.125 1.125 0 0 1 1.45.12l.773.774c.39.389.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.893.15c.543.09.94.559.94 1.109v1.094c0 .55-.397 1.02-.94 1.11l-.894.149c-.424.07-.764.383-.929.78-.165.398-.143.854.107 1.204l.527.738c.32.447.269 1.06-.12 1.45l-.774.773a1.125 1.125 0 0 1-1.449.12l-.738-.527c-.35-.25-.806-.272-1.203-.107-.398.165-.71.505-.781.929l-.149.894c-.09.542-.56.94-1.11.94h-1.094c-.55 0-1.019-.398-1.11-.94l-.148-.894c-.071-.424-.384-.764-.781-.93-.398-.164-.854-.142-1.204.108l-.738.527c-.447.32-1.06.269-1.45-.12l-.773-.774a1.125 1.125 0 0 1-.12-1.45l.527-.737c.25-.35.272-.806.108-1.204-.165-.397-.506-.71-.93-.78l-.894-.15c-.542-.09-.94-.56-.94-1.109v-1.094c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.765-.383.93-.78.165-.398.143-.854-.108-1.204l-.526-.738a1.125 1.125 0 0 1 .12-1.45l.773-.773a1.125 1.125 0 0 1 1.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.929l.15-.894Z" />
                                        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
                                    </svg>
                                    <span>Account</span>
                                </a>
                            </div>
                        </div>
                    </div>
                </>
            )}

            {/* Backdrop Overlay */}
            {isMenuOpen && (
                <div
                    className="fixed inset-0 top-12 bg-black/30 z-5 md:hidden" // Positioned below menu (z-10) but above content, starts below navbar
                    onClick={onToggleMenu}
                    aria-hidden="true"
                />
            )}
        </nav>
    );
};

export default NavBarView;
