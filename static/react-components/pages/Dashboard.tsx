import React from 'react';
import { Link } from 'react-router';
import { ArrowRight, Code, Zap, Focus, Users } from 'lucide-react';

import { Button } from '#components/reusable/Button';
import Card from '#components/reusable/Card';
import { Input } from '#components/reusable/Input';

export const Dashboard = () => {
    return <div className="flex flex-col gap-4 text-foreground overflow-y-auto">
        <div className="min-h-screen flex flex-col">
            {/* Hero Section */}
            <section className="py-20 px-4">
                <div className="max-w-4xl mx-auto flex flex-col gap-10 text-center">
                    <h1 className="text-lg md:text-6xl font-bold mb-6 bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                        Built for Solo Developers
                    </h1>
                    <p className="text-lg md:text-lg mb-8 text-foreground">
                        Project Management, Reimagined. AI-driven, code-first, and distraction-free.
                        Everything you need to ship your next big idea.
                    </p>
                    <div className="flex flex-col max-w-15 mx-auto gap-8 justify-center items-center">
                        <Button className="px-8 w-full" onClick={() => { }}>
                            <Link to="/dashboard" className='flex items-center justify-center w-full'>
                                Get Started <ArrowRight className="ml-2 h-4 w-4" />
                            </Link>
                        </Button>
                        <Button className="px-8 w-full" onClick={() => { }}>
                            <Link to="/dashboard" className='flex items-center justify-center w-full'>
                                View Demo
                            </Link>
                        </Button>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-16 px-4 ">
                <div className="mx-auto">
                    <h2 className="text-lg font-bold text-center mb-12">Why Solo Developers Choose Us</h2>

                    <div className="grid gap-6 grid-cols-2">
                        <Card className=" backdrop-blur-sm p-4">
                            <Focus className="h-12 w-12 text-primary mb-4" />
                            <h3 className="text-lg font-semibold mb-2">Stay in Your Flow</h3>
                            <p className="text-muted-foreground">Because every second counts when you're coding solo.</p>
                        </Card>

                        <Card className=" backdrop-blur-sm p-4">
                            <Zap className="h-12 w-12 text-primary mb-4" />
                            <h3 className="text-lg font-semibold mb-2">Build Faster with AI</h3>
                            <p className="text-muted-foreground">Your virtual co-pilot for smarter, faster development.</p>
                        </Card>

                        <Card className=" backdrop-blur-sm p-4">
                            <Code className="h-12 w-12 text-primary mb-4" />
                            <h3 className="text-lg font-semibold mb-2">Simplicity Over Complexity</h3>
                            <p className="text-muted-foreground">No bloated team features. Just essentials that help you ship.</p>
                        </Card>

                        <Card className=" backdrop-blur-sm p-4">
                            <Users className="h-12 w-12 text-primary mb-4" />
                            <h3 className="text-lg font-semibold mb-2">You're Never Alone</h3>
                            <p className="text-muted-foreground">Join a community of solo developers for support and camaraderie.</p>
                        </Card>
                    </div>
                </div>
            </section>

            {/* Early Access Section */}
            <section className="py-20 px-4">
                <div className="max-w-3xl mx-auto text-center">
                    <h2 className="text-lg font-bold mb-4">Be the First to Know</h2>
                    <p className="text-lg mb-8 text-muted-foreground">
                        Sign up for early access and help shape our beta.
                    </p>

                    <form className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
                        <Input
                            type="email"
                            placeholder="Your email address"
                            // value={email}
                            // onChange={(e) => setEmail(e.target.value)}
                            // required
                            className="flex-grow"
                        />
                        <Button onClick={() => { }}>Get Early Access</Button>
                    </form>
                </div>
            </section>

            <div className="h-32 w-full">  </div>

            {/* Footer */}
            <footer className="mt-auto py-8 border-t">
                <div className="max-w-6xl mx-auto px-4 text-center text-muted-foreground">
                    <p>Built by Solo Developers, for Solo Developers.</p>
                    <p className="text-sm mt-2">© 2025 TaskMaster. All rights reserved.</p>
                </div>
            </footer>
        </div>
    </div>;
};

