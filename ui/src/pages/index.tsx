import { useState } from 'react';
import { Dashboard } from '../components/Dashboard';
import { RepositoryForm } from '../components/RepositoryForm';
import { JobStatus } from '../components/JobStatus';
import { FindingsList } from '../components/FindingsList';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function Home() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [jobId, setJobId] = useState<string | null>(null);

  const handleJobSubmitted = (id: string) => {
    setJobId(id);
    setActiveTab('status');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto py-8 px-4">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Autonomous Code Improver</h1>
          <p className="text-gray-600 mt-2">
            An autonomous, multi-agent system for code improvement that ingests Git repositories, 
            builds knowledge graphs, performs analysis, suggests improvements, and creates pull requests.
          </p>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="dashboard">Dashboard</TabsTrigger>
            <TabsTrigger value="enhance">Enhance</TabsTrigger>
            <TabsTrigger value="status">Job Status</TabsTrigger>
            <TabsTrigger value="findings">Findings</TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard" className="space-y-4">
            <Dashboard />
          </TabsContent>

          <TabsContent value="enhance" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Enhance Repository</CardTitle>
                <CardDescription>
                  Submit a repository for analysis and improvement
                </CardDescription>
              </CardHeader>
              <CardContent>
                <RepositoryForm onJobSubmitted={handleJobSubmitted} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="status" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Job Status</CardTitle>
                <CardDescription>
                  Monitor the progress of your enhancement jobs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <JobStatus jobId={jobId} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="findings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Findings</CardTitle>
                <CardDescription>
                  View analysis results and recommendations
                </CardDescription>
              </CardHeader>
              <CardContent>
                <FindingsList />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
