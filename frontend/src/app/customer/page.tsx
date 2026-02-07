"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/lib/api";
import { formatPrice } from "@/lib/formatPrice";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";
import Link from 'next/link';
import { Button } from "@/components/ui/button";

interface MenuItem {
  id: string;
  title: string;
  description: string;
  price: number;
  category: string;
  image?: string;
}

interface MenuSection {
  id: string;
  name: string;
  description: string;
  items: MenuItem[];
}

export default function CustomerPage() {
  const [sections, setSections] = useState<MenuSection[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMenu();
  }, []);

  const loadMenu = async () => {
    try {
      const data = await apiService.getPublicMenu();
      if (data && data.menu) {
        setSections(data.menu);
      } else if (Array.isArray(data)) {
        // Fallback for flat array
        setSections([{
          id: 'default',
          name: 'Our Menu',
          description: 'Chef\'s selection',
          items: data
        }]);
      }
    } catch (error) {
      console.error("Failed to load menu", error);
    } finally {
      setLoading(false);
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category?.toLowerCase()) {
      case 'star': return "bg-yellow-500 hover:bg-yellow-600";
      case 'puzzle': return "bg-purple-500 hover:bg-purple-600";
      case 'plowhorse': return "bg-orange-500 hover:bg-orange-600";
      case 'dog': return "bg-red-500 hover:bg-red-600";
      default: return "bg-green-600 hover:bg-green-700 text-white";
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
        <span className="ml-2 text-lg">Loading our delicious menu...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-12">
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-16 items-center justify-between px-4">
          <Link href="/" className="font-bold text-xl flex items-center gap-2">
            🍽️ Menu
          </Link>
          <div className="text-sm text-muted-foreground mr-4">
            Explore our chef's curated selection
          </div>
        </div>
      </header>

      <main className="container py-8 px-4 max-w-7xl mx-auto">
        {sections.map((section) => (
          <div key={section.id} className="mb-12">
            <div className="mb-6">
              <h2 className="text-3xl font-bold tracking-tight text-primary mb-2">{section.name}</h2>
              {section.description && (
                <p className="text-muted-foreground">{section.description}</p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {section.items.map((item) => (
                <Card key={item.id} className="overflow-hidden hover:shadow-lg transition-all duration-300 group flex flex-col h-full">
                  <div className="aspect-video relative overflow-hidden bg-muted">
                    {item.image ? (
                      <img
                        src={item.image}
                        alt={item.title}
                        className="object-cover w-full h-full group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-4xl bg-secondary/30">
                        🍽️
                      </div>
                    )}
                    <div className="absolute top-2 right-2 flex gap-1">
                      {item.category && (
                        <Badge className={getCategoryColor(item.category)}>
                          {item.category.toUpperCase()}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <CardHeader>
                    <div className="flex justify-between items-start gap-2">
                      <CardTitle className="text-xl leading-tight">{item.title}</CardTitle>
                      <span className="text-xl font-bold text-primary shrink-0">
                        ${formatPrice(item.price)}
                      </span>
                    </div>
                    <CardDescription className="line-clamp-3 mt-2 h-12">
                      {item.description || "A delicious choice prepared with fresh ingredients."}
                    </CardDescription>
                  </CardHeader>
                  <CardFooter className="mt-auto pt-4 border-t bg-muted/20">
                    <div className="w-full text-xs text-muted-foreground text-center italic">
                      Ask your server for recommendations
                    </div>
                  </CardFooter>
                </Card>
              ))}
            </div>
            {section.items.length === 0 && (
              <div className="text-muted-foreground italic py-4">No items in this section.</div>
            )}
          </div>
        ))}

        {sections.length === 0 && (
          <div className="text-center py-20 text-muted-foreground">
            No items found on the menu currently. Please check back later!
          </div>
        )}
      </main>
    </div>
  );
}
