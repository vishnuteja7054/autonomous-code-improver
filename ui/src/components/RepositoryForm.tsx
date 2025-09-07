import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';

const formSchema = z.object({
  repoUrl: z.string().url('Please enter a valid URL'),
  branch: z.string().optional(),
  commit: z.string().optional(),
  languages: z.array(z.string()).optional(),
  paths: z.string().optional(),
  excludePatterns: z.string().optional(),
  dryRun: z.boolean().default(false),
  sinceCommit: z.string().optional(),
  only: z.string().optional(),
});

type FormValues = z.infer<typeof formSchema>;

interface RepositoryFormProps {
  onJobSubmitted: (jobId: string) => void;
}

const languageOptions = [
  { value: 'python', label: 'Python' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'java', label: 'Java' },
  { value: 'go', label: 'Go' },
  { value: 'rust', label: 'Rust' },
];

const analysisOptions = [
  { value: 'static', label: 'Static Analysis' },
  { value: 'dynamic', label: 'Dynamic Analysis' },
  { value: 'mutation', label: 'Mutation Testing' },
];

export function RepositoryForm({ onJobSubmitted }: RepositoryFormProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([]);
  const [selectedAnalysis, setSelectedAnalysis] = useState<string[]>([]);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
    setValue,
    watch,
  } = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      dryRun: true,
    },
  });

  const dryRun = watch('dryRun');

  const onSubmit = async (data: FormValues) => {
    setIsSubmitting(true);
    try {
      const response = await api.enhance({
        repoUrl: data.repoUrl,
        branch: data.branch,
        commit: data.commit,
        languages: selectedLanguages.length > 0 ? selectedLanguages : undefined,
        paths: data.paths ? data.paths.split(',').map(p => p.trim()) : undefined,
        excludePatterns: data.excludePatterns ? data.excludePatterns.split(',').map(p => p.trim()) : undefined,
        dryRun: data.dryRun,
        sinceCommit: data.sinceCommit,
        only: selectedAnalysis.length > 0 ? selectedAnalysis.join(',') : undefined,
      });

      onJobSubmitted(response.job_id);
      reset();
      setSelectedLanguages([]);
      setSelectedAnalysis([]);
    } catch (error) {
      console.error('Error submitting job:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleLanguageChange = (language: string, checked: boolean) => {
    if (checked) {
      setSelectedLanguages([...selectedLanguages, language]);
    } else {
      setSelectedLanguages(selectedLanguages.filter(lang => lang !== language));
    }
  };

  const handleAnalysisChange = (analysis: string, checked: boolean) => {
    if (checked) {
      setSelectedAnalysis([...selectedAnalysis, analysis]);
    } else {
      setSelectedAnalysis(selectedAnalysis.filter(ana => ana !== analysis));
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="repoUrl">Repository URL *</Label>
          <Input
            id="repoUrl"
            placeholder="https://github.com/example/repo"
            {...register('repoUrl')}
          />
          {errors.repoUrl && (
            <p className="text-sm text-red-500">{errors.repoUrl.message}</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="branch">Branch (optional)</Label>
          <Input
            id="branch"
            placeholder="main"
            {...register('branch')}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-2">
          <Label htmlFor="commit">Commit (optional)</Label>
          <Input
            id="commit"
            placeholder="abc123"
            {...register('commit')}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="sinceCommit">Since Commit (optional)</Label>
          <Input
            id="sinceCommit"
            placeholder="def456"
            {...register('sinceCommit')}
          />
        </div>
      </div>

      <div className="space-y-2">
        <Label>Languages (optional)</Label>
        <div className="flex flex-wrap gap-2">
          {languageOptions.map((language) => (
            <Badge
              key={language.value}
              variant={selectedLanguages.includes(language.value) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => handleLanguageChange(language.value, !selectedLanguages.includes(language.value))}
            >
              {language.label}
            </Badge>
          ))}
        </div>
      </div>

      <div className="space-y-2">
        <Label htmlFor="paths">Paths (optional, comma-separated)</Label>
        <Input
          id="paths"
          placeholder="src/,tests/"
          {...register('paths')}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="excludePatterns">Exclude Patterns (optional, comma-separated)</Label>
        <Input
          id="excludePatterns"
          placeholder="tests/,*.test.js"
          {...register('excludePatterns')}
        />
      </div>

      <div className="space-y-2">
        <Label>Analysis Types (optional)</Label>
        <div className="flex flex-wrap gap-2">
          {analysisOptions.map((analysis) => (
            <Badge
              key={analysis.value}
              variant={selectedAnalysis.includes(analysis.value) ? 'default' : 'outline'}
              className="cursor-pointer"
              onClick={() => handleAnalysisChange(analysis.value, !selectedAnalysis.includes(analysis.value))}
            >
              {analysis.label}
            </Badge>
          ))}
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <Checkbox
          id="dryRun"
          checked={dryRun}
          onCheckedChange={(checked) => setValue('dryRun', checked as boolean)}
        />
        <Label htmlFor="dryRun">Dry run (analyze without creating PR)</Label>
      </div>

      <Button type="submit" disabled={isSubmitting} className="w-full">
        {isSubmitting ? 'Submitting...' : 'Enhance Repository'}
      </Button>
    </form>
  );
}
