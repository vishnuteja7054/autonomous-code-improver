import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/lib/api';

interface JobStatusProps {
  jobId: string | null;
}

interface JobData {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  result_data: {
    findings?: {
      static?: number;
      dynamic?: number;
      mutation?: any;
    };
    proposals?: number;
    refactor_plans?: number;
    pr_id?: number;
    pr_url?: string;
  };
}

export function JobStatus({ jobId }: JobStatusProps) {
  const [job, setJob] = useState<JobData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!jobId) return;

    const fetchJobStatus = async () => {
      setLoading(true);
      try {
        const response = await api.getJobStatus(jobId);
        setJob(response);
      } catch (error) {
        console.error('Error fetching job status:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchJobStatus();

    // Poll for updates if job is not completed
    const interval = setInterval(() => {
      if (job && (job.status === 'pending' || job.status === 'running')) {
        fetchJobStatus();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [jobId]);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
        return 'secondary';
      case 'failed':
        return 'destructive';
      case 'cancelled':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!jobId) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">Submit a job to see its status here</p>
        </CardContent>
      </Card>
    );
  }

  if (loading && !job) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!job) {
    return (
      <Card>
        <CardContent className="pt-6">
          <p className="text-center text-muted-foreground">Job not found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Job Status</CardTitle>
              <CardDescription>Job ID: {job.id}</CardDescription>
            </div>
            <Badge variant={getStatusBadgeVariant(job.status)}>
              {job.status}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Progress</span>
                <span>{Math.round(job.progress * 100)}%</span>
              </div>
              <Progress value={job.progress * 100} className="w-full" />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div>
                <span className="text-muted-foreground">Created:</span>
                <div>{formatDateTime(job.created_at)}</div>
              </div>
              {job.started_at && (
                <div>
                  <span className="text-muted-foreground">Started:</span>
                  <div>{formatDateTime(job.started_at)}</div>
                </div>
              )}
              {job.completed_at && (
                <div>
                  <span className="text-muted-foreground">Completed:</span>
                  <div>{formatDateTime(job.completed_at)}</div>
                </div>
              )}
            </div>

            {job.error_message && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <p className="text-sm text-red-800">{job.error_message}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {job.status === 'completed' && job.result_data && (
        <Tabs defaultValue="results" className="w-full">
          <TabsList>
            <TabsTrigger value="results">Results</TabsTrigger>
            <TabsTrigger value="findings">Findings</TabsTrigger>
            <TabsTrigger value="proposals">Proposals</TabsTrigger>
          </TabsList>

          <TabsContent value="results" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Analysis Results</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {job.result_data.findings?.static !== undefined && (
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-2xl font-bold">{job.result_data.findings.static}</div>
                      <div className="text-sm text-muted-foreground">Static Findings</div>
                    </div>
                  )}
                  
                  {job.result_data.findings?.dynamic !== undefined && (
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-2xl font-bold">{job.result_data.findings.dynamic}</div>
                      <div className="text-sm text-muted-foreground">Dynamic Findings</div>
                    </div>
                  )}
                  
                  {job.result_data.findings?.mutation && (
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-2xl font-bold">
                        {Math.round(job.result_data.findings.mutation.mutation_score * 100)}%
                      </div>
                      <div className="text-sm text-muted-foreground">Mutation Score</div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="findings" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Findings Summary</CardTitle>
              </CardHeader>
              <CardContent>
                {job.result_data.findings ? (
                  <div className="space-y-2">
                    {job.result_data.findings.static !== undefined && (
                      <div className="flex justify-between">
                        <span>Static Analysis Issues</span>
                        <Badge variant="outline">{job.result_data.findings.static}</Badge>
                      </div>
                    )}
                    {job.result_data.findings.dynamic !== undefined && (
                      <div className="flex justify-between">
                        <span>Dynamic Analysis Issues</span>
                        <Badge variant="outline">{job.result_data.findings.dynamic}</Badge>
                      </div>
                    )}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No findings data available</p>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="proposals" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Feature Proposals</CardTitle>
              </CardHeader>
              <CardContent>
                {job.result_data.proposals !== undefined ? (
                  <div className="text-center">
                    <div className="text-2xl font-bold">{job.result_data.proposals}</div>
                    <div className="text-sm text-muted-foreground">Feature proposals generated</div>
                  </div>
                ) : (
                  <p className="text-muted-foreground">No proposals data available</p>
                )}
              </CardContent>
            </Card>

            {job.result_data.refactor_plans !== undefined && (
              <Card>
                <CardHeader>
                  <CardTitle>Refactoring Plans</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-center">
                    <div className="text-2xl font-bold">{job.result_data.refactor_plans}</div>
                    <div className="text-sm text-muted-foreground">Refactoring plans created</div>
                  </div>
                </CardContent>
              </Card>
            )}

            {job.result_data.pr_id && (
              <Card>
                <CardHeader>
                  <CardTitle>Pull Request</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>PR ID</span>
                      <Badge variant="outline">#{job.result_data.pr_id}</Badge>
                    </div>
                    {job.result_data.pr_url && (
                      <Button asChild className="w-full">
                        <a href={job.result_data.pr_url} target="_blank" rel="noopener noreferrer">
                          View Pull Request
                        </a>
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
