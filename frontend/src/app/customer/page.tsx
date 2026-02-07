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
  category: string; // 'star', 'dog', 'puzzle', 'plowhorse' or other
  image?: string;
}

export default function CustomerPage() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMenu();
  }, []);

  const loadMenu = async () => {
    try {
      const data = await apiService.getPublicMenu();
      // Adjust depending on API response structure. 
      // If it returns { menu: [...] } or just [...]
      if (Array.isArray(data)) {
        setItems(data);
      } else if (data.menu) {
        setItems(data.menu);
      } else if (data.items) {
          setItems(data.items);
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
      default: return "bg-green-600 hover:bg-green-700";
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
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="font-bold text-xl flex items-center gap-2">
            🍽️ Menu
          </Link>
          <div className="text-sm text-muted-foreground mr-4">
              Explore our chef's curated selection
          </div>
        </div>
      </header>
      
      <main className="container py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((item) => (
            <Card key={item.id} className="overflow-hidden hover:shadow-lg transition-all duration-300 group">
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
                <div className="flex justify-between items-start">
                    <CardTitle className="text-xl">{item.title}</CardTitle>
                    <span className="text-lg font-bold text-primary">
                        ${formatPrice(item.price)}
                    </span>
                </div>
                <CardDescription className="line-clamp-2">
                    {item.description || "A delicious choice prepared with fresh ingredients."}
                </CardDescription>
              </CardHeader>
              <CardFooter>
                 {/* No Actions for Customer View, purely informational */}
                 <div className="w-full text-xs text-muted-foreground text-center italic">
                     Ask your server for details
                 </div>
              </CardFooter>
            </Card>
          ))}
        </div>
        
        {items.length === 0 && (
             <div className="text-center py-20 text-muted-foreground">
                 No items found on the menu currently. Please check back later!
             </div>
        )}
      </main>
    </div>
  );
}
