"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { apiService } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function StaffLoginPage() {
  const [step, setStep] = useState(1); // 1: Credentials, 2: OTP
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [sessionToken, setSessionToken] = useState("");
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  const handleLoginStep1 = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await apiService.loginStep1({ email, password });
      setSessionToken(response.session_token);
      toast.success(response.message || "OTP sent to your phone");
      setStep(2);
    } catch (error: any) {
      toast.error(error.message || "Invalid credentials");
    } finally {
      setLoading(false);
    }
  };

  const handleLoginStep2 = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await apiService.loginStep2({ session_token: sessionToken, otp });
      toast.success("Welcome back, staff member!");
      router.push("/staff/orders");
    } catch (error: any) {
      toast.error(error.message || "Invalid OTP");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 p-4">
      <Card className="w-full max-w-md border-orange-200">
        <CardHeader>
          <CardTitle className="text-2xl text-orange-700">Staff Portal</CardTitle>
          <CardDescription>
            {step === 1 ? "Login to access the order system." : "Enter the OTP sent to your phone."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {step === 1 ? (
            <form onSubmit={handleLoginStep1} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Staff ID / Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="staff@restaurant.com"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">PIN / Password</Label>
                <Input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <Button type="submit" className="w-full bg-orange-600 hover:bg-orange-700" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Next
              </Button>
            </form>
          ) : (
            <form onSubmit={handleLoginStep2} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="otp">One-Time Password (OTP)</Label>
                <Input
                  id="otp"
                  type="text"
                  placeholder="ABC12DEF"
                  required
                  value={otp}
                  onChange={(e) => setOtp(e.target.value)}
                  maxLength={8}
                  className="text-center text-lg tracking-widest"
                />
              </div>
              <Button type="submit" className="w-full bg-orange-600 hover:bg-orange-700" disabled={loading}>
                {loading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Start Shift
              </Button>
               <Button variant="ghost" className="w-full" onClick={() => setStep(1)} disabled={loading}>
                Back to Login
              </Button>
            </form>
          )}
        </CardContent>
        <CardFooter className="flex justify-center text-sm text-muted-foreground">
            <a href="/" className="hover:underline">Back to Main Menu</a>
        </CardFooter>
      </Card>
    </div>
  );
}
