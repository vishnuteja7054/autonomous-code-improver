import { useEffect, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';

interface DashboardStats {
  totalRepositories: number;
  totalJobs: number;
  completedJobs: number;
  totalFindings: number;
  findingsByType: Record<string, number>;
  recentJobs: Array<{
    id: string;
    repoUrl: string;
    status: string;
    createdAt: string;
  }>;
}

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats>({
    totalRepositories: 0,
    totalJobs: 0,
    completedJobs: 0,
    totalFindings: 0,
    findingsByType: {},
    recentJobs: []
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        // In a real implementation, you would fetch actual stats from the API
        // For now, we'll use mock data
        const mockStats: DashboardStats = {
          totalRepositories: 12,
          totalJobs: 24,
          completedJobs: 18,
          totalFindings: 156,
          findingsByType: {
            security: 42,
            performance: 38,
            maintainability: 45,
            reliability: 31
          },
          recentJobs: [
            { id: '1', repoUrl: 'https://github.com/example/repo1', status: 'completed', createdAt: '2023-06-15T10:30:00Z' },
            { id: '2', repoUrl: 'https://github.com/example/repo2', status: 'running', createdAt: '2023-06-15T09:15:00Z' },
            { id: '3', repoUrl: 'https://github.com/example/repo3', status: 'failed', createdAt: '2023-06-14T16:45:00Z' },
            { id: '4', repoUrl: 'https://github.com/example/repo4', status: 'completed', createdAt: '2023-06-14T14:20:00Z' }
          ]
        };
        
        setStats(mockStats);
      } catch (error) {
        console.error('Error fetching dashboard stats:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const getStatusBadgeVariant = (status: string) => {
    switch (status) {
      case 'completed':
        return 'default';
      case 'running':
        return 'secondary';
      case 'failed':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardHeader className="pb-2">
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
            </CardHeader>
            <CardContent>
              <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Repositories</CardTitle>
            <div className="h-4 w-4 text-muted-foreground"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalRepositories}</div>
            <p className="text-xs text-muted-foreground">Total repositories analyzed</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Jobs</CardTitle>
            <div className="h-4 w-4 text-muted-foreground"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalJobs}</div>
            <p className="text-xs text-muted-foreground">
              {stats.completedJobs} completed ({Math.round((stats.completedJobs / stats.totalJobs) * 100)}%)
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Findings</CardTitle>
            <div className="h-4 w-4 text-muted-foreground"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalFindings}</div>
            <p className="text-xs text-muted-foreground">Total issues identified</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
            <div className="h-4 w-4 text-muted-foreground"></div>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {stats.totalJobs > 0 ? Math.round((stats.completedJobs / stats.totalJobs) * 100) : 0}%
            </div>
            <p className="text-xs text-muted-foreground">Job completion rate</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Findings by Type</CardTitle>
            <CardDescription>Distribution of identified issues</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats.findingsByType).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                    <span className="capitalize">{type}</span>
                  </div>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Recent Jobs</CardTitle>
            <CardDescription>Latest enhancement jobs</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {stats.recentJobs.map((job) => (
                <div key={job.id} className="flex items-center justify-between">
                  <div>
                    <div className="font-medium truncate max-w-[200px]" title={job.repoUrl}>
                      {job.repoUrl.split('/').pop()}
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(job.createdAt).toLocaleString()}
                    </div>
                  </div>
                  <Badge variant={getStatusBadgeVariant(job.status)}>
                    {job.status}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
