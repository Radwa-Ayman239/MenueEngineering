"use client";

import { useEffect, useState } from "react";
import { apiService } from "@/lib/api";
import { formatPrice } from "@/lib/formatPrice";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Loader2, Minus, Plus, Trash2, ShoppingCart } from "lucide-react";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

interface MenuItem {
  id: string;
  title: string;
  price: number;
  category: string;
}

interface CartItem extends MenuItem {
  quantity: number;
}

export default function StaffOrderPage() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const router = useRouter();

  useEffect(() => {
    loadMenu();
  }, []);

  const loadMenu = async () => {
    try {
      // Request up to 100 items to cover most menus without complex pagination UI for now
      const data = await apiService.getMenuItems({ is_active: true, page_size: 100 }) as any;
      if (Array.isArray(data)) setItems(data);
      else if (data.results) setItems(data.results);
    } catch (error) {
      toast.error("Failed to load menu items");
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (item: MenuItem) => {
    setCart(prev => {
      const existing = prev.find(i => i.id === item.id);
      if (existing) {
        return prev.map(i => i.id === item.id ? { ...i, quantity: i.quantity + 1 } : i);
      }
      return [...prev, { ...item, quantity: 1 }];
    });
  };

  const removeFromCart = (id: string) => {
    setCart(prev => prev.filter(i => i.id !== id));
  };

  const updateQuantity = (id: string, delta: number) => {
    setCart(prev => prev.map(i => {
      if (i.id === id) {
        const newQty = i.quantity + delta;
        return newQty > 0 ? { ...i, quantity: newQty } : i;
      }
      return i;
    }));
  };

  const getTotal = () => {
    return cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  };

  const handleCheckout = async () => {
    if (cart.length === 0) return;
    setSubmitting(true);
    try {
      const orderData = {
        items: cart.map(i => ({ item: i.id, quantity: i.quantity })),
        total_price: getTotal()
      };
      await apiService.createOrder(orderData);
      toast.success("Order submitted successfully!");
      setCart([]);
    } catch (error: any) {
      toast.error("Failed to submit order: " + (error.message || "Unknown error"));
    } finally {
      setSubmitting(false);
    }
  };

  const logout = () => {
      apiService.logout();
      router.push("/");
  };

  if (loading) return <div className="flex h-screen items-center justify-center"><Loader2 className="animate-spin" /></div>;

  return (
    <div className="flex h-screen bg-muted/20 overflow-hidden">
      {/* Menu Area */}
      <div className="flex-1 flex flex-col h-full p-4 overflow-hidden">
        <header className="flex justify-between items-center mb-4">
           <h1 className="text-2xl font-bold">Staff Ordering</h1>
           <Button variant="ghost" onClick={logout}>Logout</Button>
        </header>

        <ScrollArea className="flex-1 pr-4">
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 pb-20">
            {items.map((item) => (
              <Card 
                key={item.id} 
                className="cursor-pointer hover:border-primary transition-colors active:scale-95 duration-100"
                onClick={() => addToCart(item)}
              >
                <CardContent className="p-4 flex flex-col justify-between h-32">
                  <div className="font-medium line-clamp-2">{item.title}</div>
                  <div className="flex justify-between items-end">
                    <span className="font-bold text-lg">${formatPrice(item.price)}</span>
                    <Badge variant="outline" className="text-xs uppercase">{item.category?.slice(0,3)}</Badge>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </ScrollArea>
      </div>

      {/* Cart Sidebar */}
      <div className="w-[400px] border-l bg-background flex flex-col h-full shadow-xl z-20">
        <div className="p-4 border-b flex items-center gap-2 bg-muted/10">
           <ShoppingCart className="h-5 w-5" />
           <h2 className="font-semibold text-lg">Current Order</h2>
        </div>

        <ScrollArea className="flex-1 p-4">
           {cart.length === 0 ? (
               <div className="h-40 flex items-center justify-center text-muted-foreground italic">
                   Order is empty
               </div>
           ) : (
               <div className="space-y-4">
                   {cart.map((item) => (
                       <div key={item.id} className="flex justify-between items-center group">
                           <div className="flex-1">
                               <div className="font-medium text-sm">{item.title}</div>
                               <div className="text-xs text-muted-foreground">${formatPrice(item.price)} each</div>
                           </div>
                           <div className="flex items-center gap-2">
                               <Button variant="outline" size="icon" className="h-6 w-6" onClick={() => updateQuantity(item.id, -1)}>
                                   <Minus className="h-3 w-3" />
                               </Button>
                               <span className="w-4 text-center text-sm">{item.quantity}</span>
                               <Button variant="outline" size="icon" className="h-6 w-6" onClick={() => updateQuantity(item.id, 1)}>
                                   <Plus className="h-3 w-3" />
                               </Button>
                               <Button variant="ghost" size="icon" className="h-6 w-6 text-destructive hover:bg-destructive/10" onClick={() => removeFromCart(item.id)}>
                                   <Trash2 className="h-3 w-3" />
                               </Button>
                           </div>
                       </div>
                   ))}
               </div>
           )}
        </ScrollArea>

        <div className="p-4 border-t bg-muted/5 space-y-4">
            <div className="flex justify-between text-lg font-bold">
                <span>Total</span>
                <span>${formatPrice(getTotal())}</span>
            </div>
            <Button className="w-full text-lg h-12" size="lg" disabled={cart.length === 0 || submitting} onClick={handleCheckout}>
                {submitting ? <Loader2 className="animate-spin mr-2" /> : "Submit Order"}
            </Button>
        </div>
      </div>
    </div>
  );
}
