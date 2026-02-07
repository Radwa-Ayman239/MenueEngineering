"use client";

import { useEffect, useState, useCallback } from "react";
import { apiService } from "@/lib/api";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Loader2, Plus, RefreshCw, TrendingUp, Search, ChevronLeft, ChevronRight, DollarSign, BarChart3 } from "lucide-react";
import { formatPrice } from "@/lib/formatPrice";
import { toast } from "sonner";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useRouter } from "next/navigation";

interface MenuItem {
  id: string;
  title: string;
  category: string;
  price: number;
  description: string;
  is_active: boolean;
}

export default function ManagerDashboard() {
  const [items, setItems] = useState<MenuItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [menuLoading, setMenuLoading] = useState(false);
  const [newItem, setNewItem] = useState({ title: "", price: "", category: "star", description: "" });
  const [report, setReport] = useState<any>(null);
  const [aiSuggestions, setAiSuggestions] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  
  // Pagination & Search State
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const pageSize = 10; // Adjust as needed
  
  const router = useRouter();

  // Initial Data Load
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Fetch Menu Items when page or search changes
  useEffect(() => {
    loadMenuData();
  }, [page, searchQuery]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [statsData, reportData, suggestions] = await Promise.all([
        apiService.getMenuStats().catch(() => null),
        apiService.getOwnerReport('daily').catch(() => null),
        apiService.getSalesSuggestions().catch(() => [])
      ]);
      
      setStats(statsData);
      setReport(reportData || {});
      console.log("Suggestions received:", suggestions);
      setAiSuggestions(suggestions || []);
    } catch (error) {
      console.error("Failed to load dashboard data", error);
      toast.error("Failed to load dashboard data.");
    } finally {
      setLoading(false);
    }
  };

  const loadMenuData = async () => {
      setMenuLoading(true);
      try {
          const params = {
              page,
              page_size: pageSize,
              search: searchQuery
          };
          const data = await apiService.getMenuItems(params);
          
          if (data.results) {
              setItems(data.results);
              setTotalPages(Math.ceil(data.count / pageSize));
          } else {
              setItems(data || []); // Fallback if no pagination
          }
      } catch (error) {
          console.error("Failed to load menu items", error);
      } finally {
          setMenuLoading(false);
      }
  };

  const handleCreateItem = async () => {
    try {
      await apiService.createMenuItem({
          ...newItem,
          price: parseFloat(newItem.price),
          is_active: true
      });
      toast.success("Menu item created successfully!");
      setNewItem({ title: "", price: "", category: "star", description: "" });
      loadMenuData(); // Refresh list
      loadDashboardData(); // Refresh stats
    } catch (error) {
      toast.error("Failed to create item.");
    }
  };
  
  const handleDeleteItem = async (id: string) => {
      try {
          await apiService.deleteMenuItem(id);
          toast.success("Item deleted");
          loadMenuData();
          loadDashboardData();
      } catch (error) {
          toast.error("Failed to delete item");
      }
  };

  const logout = () => {
      apiService.logout();
      router.push("/");
  };

  if (loading) {
     return (
         <div className="flex h-screen items-center justify-center">
             <Loader2 className="h-8 w-8 animate-spin" />
         </div>
     );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Manager Dashboard</h1>
          <p className="text-muted-foreground">Manage your menu and view insights.</p>
        </div>
        <div className="flex gap-2">
            <Button variant="outline" onClick={() => { loadDashboardData(); loadMenuData(); }}>
                <RefreshCw className="mr-2 h-4 w-4" /> Refresh
            </Button>
            <Button variant="destructive" onClick={logout}>
                Logout
            </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="items">Menu Items</TabsTrigger>
          <TabsTrigger value="report">AI Report</TabsTrigger>
          <TabsTrigger value="suggestions">Suggestions</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Total Items</CardTitle>
                        <BarChart3 className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{stats?.total_items || 0}</div>
                        <p className="text-xs text-muted-foreground">Active menu items</p>
                    </CardContent>
                </Card>
                <Card>
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Probable Total Profit</CardTitle>
                        <DollarSign className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">${formatPrice(stats?.overall_profit || 0)}</div>
                        <p className="text-xs text-muted-foreground">Based on current volume</p>
                    </CardContent>
                </Card>
            </div>

            <h3 className="text-lg font-medium mt-6 mb-4">Category Breakdown</h3>
            <div className="grid gap-4 md:grid-cols-4">
                {['star', 'plowhorse', 'puzzle', 'dog'].map(cat => {
                    const catStat = stats?.categories?.find((s: any) => s.category?.toLowerCase() === cat);
                    return (
                        <Card key={cat}>
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm font-medium capitalize">{cat}s</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{catStat?.count || 0}</div>
                                <p className="text-xs text-muted-foreground">
                                    {(cat === 'star' && "High Profit, High Pop") ||
                                     (cat === 'plowhorse' && "Low Profit, High Pop") ||
                                     (cat === 'puzzle' && "High Profit, Low Pop") ||
                                     (cat === 'dog' && "Low Profit, Low Pop")}
                                </p>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>
        </TabsContent>

        <TabsContent value="items" className="space-y-4">
             <div className="flex flex-col sm:flex-row justify-between gap-4">
                <div className="relative w-full sm:w-64">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input 
                        placeholder="Search items..." 
                        className="pl-8" 
                        value={searchQuery}
                        onChange={(e) => { setSearchQuery(e.target.value); setPage(1); }}
                    />
                </div>
                
                <Dialog>
                    <DialogTrigger asChild>
                        <Button><Plus className="mr-2 h-4 w-4" /> Add Item</Button>
                    </DialogTrigger>
                    <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                            <DialogTitle>Add New Item</DialogTitle>
                            <DialogDescription>Create a new dish for your menu.</DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="title" className="text-right">Title</Label>
                                <Input 
                                    id="title" 
                                    value={newItem.title} 
                                    onChange={(e) => setNewItem({...newItem, title: e.target.value})}
                                    className="col-span-3" 
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="price" className="text-right">Price</Label>
                                <Input 
                                    id="price" 
                                    type="number" 
                                    value={newItem.price} 
                                    onChange={(e) => setNewItem({...newItem, price: e.target.value})}
                                    className="col-span-3" 
                                />
                            </div>
                            <div className="grid grid-cols-4 items-center gap-4">
                                <Label htmlFor="category" className="text-right">Category</Label>
                                <Select 
                                    onValueChange={(val) => setNewItem({...newItem, category: val})}
                                    defaultValue={newItem.category}
                                >
                                    <SelectTrigger className="col-span-3">
                                        <SelectValue placeholder="Select Category" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value="star">Star</SelectItem>
                                        <SelectItem value="plowhorse">Plowhorse</SelectItem>
                                        <SelectItem value="puzzle">Puzzle</SelectItem>
                                        <SelectItem value="dog">Dog</SelectItem>
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>
                        <DialogFooter>
                            <Button onClick={handleCreateItem}>Save changes</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
             </div>

             <Card>
                 <CardHeader>
                     <CardTitle>Menu Items</CardTitle>
                     <CardDescription>Manage your current menu offerings.</CardDescription>
                 </CardHeader>
                 <CardContent>
                    {menuLoading ? (
                        <div className="flex justify-center py-8"><Loader2 className="animate-spin" /></div>
                    ) : (
                     <>
                      <Table>
                          <TableHeader>
                              <TableRow>
                                  <TableHead>Title</TableHead>
                                  <TableHead>Category</TableHead>
                                  <TableHead>Price</TableHead>
                                  <TableHead className="text-right">Actions</TableHead>
                              </TableRow>
                          </TableHeader>
                          <TableBody>
                              {items.length > 0 ? items.map((item) => (
                                  <TableRow key={item.id}>
                                      <TableCell className="font-medium">{item.title}</TableCell>
                                      <TableCell>
                                          <Badge variant={item.category === 'star' ? "default" : "secondary"}>
                                             {item.category?.toUpperCase() || "UNKNOWN"}
                                          </Badge>
                                      </TableCell>
                                      <TableCell>${formatPrice(item.price)}</TableCell>
                                      <TableCell className="text-right">
                                          <Button variant="ghost" size="sm" onClick={() => handleDeleteItem(item.id)}>Delete</Button>
                                      </TableCell>
                                  </TableRow>
                              )) : (
                                  <TableRow>
                                      <TableCell colSpan={4} className="text-center h-24">
                                          No items found.
                                      </TableCell>
                                  </TableRow>
                              )}
                          </TableBody>
                      </Table>
                      
                      {/* Pagination Controls */}
                      <div className="flex items-center justify-end space-x-2 py-4">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setPage(p => Math.max(1, p - 1))}
                          disabled={page === 1 || menuLoading}
                        >
                          <ChevronLeft className="h-4 w-4" />
                          Previous
                        </Button>
                        <div className="text-sm font-medium">
                            Page {page} of {totalPages}
                        </div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                          disabled={page === totalPages || menuLoading}
                        >
                          Next
                          <ChevronRight className="h-4 w-4" />
                        </Button>
                      </div>
                     </>
                    )}
                 </CardContent>
             </Card>
        </TabsContent>

        <TabsContent value="report" className="space-y-4">
            <Card>
                <CardHeader>
                    <CardTitle>Daily Executive Summary</CardTitle>
                    <CardDescription>AI-generated report for today.</CardDescription>
                </CardHeader>
                <CardContent>
                    <p className="text-sm text-foreground/80 leading-relaxed whitespace-pre-wrap">
                        {report?.executive_summary || "Report generation in progress..."}
                    </p>
                </CardContent>
            </Card>
        </TabsContent>

        <TabsContent value="suggestions" className="space-y-4">
            <Card>
                <CardHeader>
                    <CardTitle>AI Insights & Suggestions</CardTitle>
                    <CardDescription>Recommendations to improve menu performance.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="space-y-4">
                        {aiSuggestions.length > 0 ? aiSuggestions.map((suggestion, idx) => (
                            <div key={idx} className="flex items-start space-x-4 rounded-md border p-4">
                                <TrendingUp className="mt-px h-5 w-5" />
                                <div className="space-y-1">
                                    <p className="text-sm font-medium leading-none">
                                        {suggestion.title || "Optimization Tip"}
                                    </p>
                                    <p className="text-sm text-muted-foreground">
                                        {suggestion.description || "Analyze recent sales data to identify underperforming items."}
                                    </p>
                                </div>
                            </div>
                        )) : (
                            <p className="text-muted-foreground py-8 text-center">No AI suggestions available at the moment. Try generating a report.</p>
                        )}
                        <Button className="w-full" variant="secondary" onClick={() => toast.info("Generative AI analysis started...")}>
                            Generate Fresh Insights
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </TabsContent>
        
      </Tabs>
    </div>
  );
}
