import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/lib/api';

interface Finding {
  id: string;
  type: string;
  severity: string;
  title: string;
  description: string;
  file_path?: string;
  start_line?: number;
  end_line?: number;
  created_at: string;
  resolved: boolean;
}

export function FindingsList() {
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    type: 'all',
    severity: 'all',
    resolved: 'all',
    search: '',
  });

  useEffect(() => {
    const fetchFindings = async () => {
      setLoading(true);
      try {
        // In a real implementation, you would fetch actual findings from the API
        // For now, we'll use mock data
        const mockFindings: Finding[] = [
          {
            id: '1',
            type: 'security',
            severity: 'high',
            title: 'SQL Injection Vulnerability',
            description: 'Potential SQL injection vulnerability in query construction',
            file_path: 'src/database.py',
            start_line: 42,
            end_line: 45,
            created_at: '2023-06-15T10:30:00Z',
            resolved: false,
          },
          {
            id: '2',
            type: 'performance',
            severity: 'medium',
            title: 'Inefficient Loop',
            description: 'Loop has O(n^2) complexity, consider optimizing',
            file_path: 'src/processing.py',
            start_line: 78,
            end_line: 85,
            created_at: '2023-06-15T09:15:00Z',
            resolved: false,
          },
          {
            id: '3',
            type: 'style',
            severity: 'low',
            title: 'Missing Docstring',
            description: 'Function is missing a docstring',
            file_path: 'src/utils.py',
            start_line: 15,
            end_line: 20,
            created_at: '2023-06-14T16:45:00Z',
            resolved: true,
          },
          {
            id: '4',
            type: 'security',
            severity: 'critical',
            title: 'Hardcoded Secret',
            description: 'Hardcoded API key found in source code',
            file_path: 'src/config.py',
            start_line: 12,
            end_line: 12,
            created_at: '2023-06-14T14:20:00Z',
            resolved: false,
          },
          {
            id: '5',
            type: 'maintainability',
            severity: 'medium',
            title: 'Duplicate Code',
            description: 'Duplicate code detected in multiple functions',
            file_path: 'src/helpers.py',
            start_line: 25,
            end_line: 40,
            created_at: '2023-06-13T11:30:00Z',
            resolved: false,
          },
        ];
        
        setFindings(mockFindings);
      } catch (error) {
        console.error('Error fetching findings:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchFindings();
  }, []);

  const getSeverityBadgeVariant = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'destructive';
      case 'high':
        return 'destructive';
      case 'medium':
        return 'secondary';
      case 'low':
        return 'outline';
      default:
        return 'outline';
    }
  };

  const getTypeBadgeVariant = (type: string) => {
    switch (type) {
      case 'security':
        return 'destructive';
      case 'performance':
        return 'secondary';
      case 'style':
        return 'outline';
      case 'maintainability':
        return 'default';
      default:
        return 'outline';
    }
  };

  const filteredFindings = findings.filter((finding) => {
    return (
      (filter.type === 'all' || finding.type === filter.type) &&
      (filter.severity === 'all' || finding.severity === filter.severity) &&
      (filter.resolved === 'all' || 
        (filter.resolved === 'resolved' && finding.resolved) ||
        (filter.resolved === 'unresolved' && !finding.resolved)) &&
      (filter.search === '' || 
        finding.title.toLowerCase().includes(filter.search.toLowerCase()) ||
        finding.description.toLowerCase().includes(filter.search.toLowerCase()) ||
        (finding.file_path && finding.file_path.toLowerCase().includes(filter.search.toLowerCase())))
    );
  });

  const formatDateTime = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded animate-pulse"></div>
                <div className="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Filter Findings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <Select value={filter.type} onValueChange={(value) => setFilter({...filter, type: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value="security">Security</SelectItem>
                  <SelectItem value="performance">Performance</SelectItem>
                  <SelectItem value="style">Style</SelectItem>
                  <SelectItem value="maintainability">Maintainability</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Select value={filter.severity} onValueChange={(value) => setFilter({...filter, severity: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Severity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Severities</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Select value={filter.resolved} onValueChange={(value) => setFilter({...filter, resolved: value})}>
                <SelectTrigger>
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="unresolved">Unresolved</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div>
              <Input
                placeholder="Search findings..."
                value={filter.search}
                onChange={(e) => setFilter({...filter, search: e.target.value})}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="all" className="w-full">
        <TabsList>
          <TabsTrigger value="all">All ({filteredFindings.length})</TabsTrigger>
          <TabsTrigger value="unresolved">
            Unresolved ({filteredFindings.filter(f => !f.resolved).length})
          </TabsTrigger>
          <TabsTrigger value="resolved">
            Resolved ({filteredFindings.filter(f => f.resolved).length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {filteredFindings.length === 0 ? (
            <Card>
              <CardContent className="pt-6">
                <p className="text-center text-muted-foreground">No findings match your filters</p>
              </CardContent>
            </Card>
          ) : (
            filteredFindings.map((finding) => (
              <Card key={finding.id}>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="space-y-1">
                      <CardTitle className="text-lg">{finding.title}</CardTitle>
                      <div className="flex items-center space-x-2">
                        <Badge variant={getTypeBadgeVariant(finding.type)}>
                          {finding.type}
                        </Badge>
                        <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                          {finding.severity}
                        </Badge>
                        {finding.resolved && <Badge variant="outline">Resolved</Badge>}
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {formatDateTime(finding.created_at)}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <p>{finding.description}</p>
                    
                    {finding.file_path && (
                      <div className="text-sm">
                        <span className="text-muted-foreground">File:</span>{' '}
                        <code className="bg-gray-100 px-1 py-0.5 rounded">
                          {finding.file_path}
                        </code>
                        {finding.start_line && finding.end_line && (
                          <span>
                            {' '}(Lines {finding.start_line}-{finding.end_line})
                          </span>
                        )}
                      </div>
                    )}
                    
                    <div className="flex justify-end">
                      {!finding.resolved && (
                        <Button variant="outline" size="sm">
                          Mark as Resolved
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        <TabsContent value="unresolved" className="space-y-4">
          {filteredFindings.filter(f => !f.resolved).map((finding) => (
            <Card key={finding.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">{finding.title}</CardTitle>
                    <div className="flex items-center space-x-2">
                      <Badge variant={getTypeBadgeVariant(finding.type)}>
                        {finding.type}
                      </Badge>
                      <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                        {finding.severity}
                      </Badge>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDateTime(finding.created_at)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p>{finding.description}</p>
                  
                  {finding.file_path && (
                    <div className="text-sm">
                      <span className="text-muted-foreground">File:</span>{' '}
                      <code className="bg-gray-100 px-1 py-0.5 rounded">
                        {finding.file_path}
                      </code>
                      {finding.start_line && finding.end_line && (
                        <span>
                          {' '}(Lines {finding.start_line}-{finding.end_line})
                        </span>
                      )}
                    </div>
                  )}
                  
                  <div className="flex justify-end">
                    <Button variant="outline" size="sm">
                      Mark as Resolved
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        <TabsContent value="resolved" className="space-y-4">
          {filteredFindings.filter(f => f.resolved).map((finding) => (
            <Card key={finding.id}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-lg">{finding.title}</CardTitle>
                    <div className="flex items-center space-x-2">
                      <Badge variant={getTypeBadgeVariant(finding.type)}>
                        {finding.type}
                      </Badge>
                      <Badge variant={getSeverityBadgeVariant(finding.severity)}>
                        {finding.severity}
                      </Badge>
                      <Badge variant="outline">Resolved</Badge>
                    </div>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDateTime(finding.created_at)}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <p>{finding.description}</p>
                  
                  {finding.file_path && (
                    <div className="text-sm">
                      <span className="text-muted-foreground">File:</span>{' '}
                      <code className="bg-gray-100 px-1 py-0.5 rounded">
                        {finding.file_path}
                      </code>
                      {finding.start_line && finding.end_line && (
                        <span>
                          {' '}(Lines {finding.start_line}-{finding.end_line})
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  );
}
