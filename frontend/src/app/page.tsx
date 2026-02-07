/**
 * File: page.tsx
 * Authors: Hamdy El-Madbouly, Hajar
 * Description: Landing page for the Menu Engineering application.
 * Provides the main entry point with navigation cards for different user roles:
 * - Customer: View public menu
 * - Staff: POS and order management
 * - Manager: Dashboard and analytics
 */

import Link from 'next/link';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="min-h-screen bg-background flex flex-col items-center justify-center p-4">
      <div className="text-center mb-12 space-y-4">
        <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">
          🍽️ Menu Engineering System
        </h1>
        <p className="text-xl text-muted-foreground">
          Select your role to continue
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl w-full px-4">
        {/* Customer Access */}
        <Card className="hover:shadow-lg transition-all duration-300 border-primary/20 hover:border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              👤 Customer
            </CardTitle>
            <CardDescription>
              View our delicious menu and discover new favorites.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/customer" className="w-full">
              <Button className="w-full" size="lg">
                View Menu
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Staff Access */}
        <Card className="hover:shadow-lg transition-all duration-300 border-primary/20 hover:border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              👨‍🍳 Staff
            </CardTitle>
            <CardDescription>
              Record orders and manage table service.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/staff/login" className="w-full">
              <Button variant="outline" className="w-full" size="lg">
                Staff Login
              </Button>
            </Link>
          </CardContent>
        </Card>

        {/* Manager Access */}
        <Card className="hover:shadow-lg transition-all duration-300 border-primary/20 hover:border-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              📊 Manager
            </CardTitle>
            <CardDescription>
              Analyze performance, manage menu items, and view reports.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Link href="/manager/login" className="w-full">
              <Button variant="secondary" className="w-full" size="lg">
                Manager Dashboard
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>

      <footer className="mt-16 text-sm text-muted-foreground">
        Powered by AI-Driven Menu Engineering
      </footer>
    </div>
  );
}
