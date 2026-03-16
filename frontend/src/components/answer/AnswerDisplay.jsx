import { useEffect, useRef } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import Card from '../shared/GlassCard';

export default function AnswerDisplay({ answer, isStreaming }) {
  const ref = useRef(null);

  useEffect(() => {
    if (answer && ref.current) {
      ref.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, [answer ? 'has-answer' : 'no-answer']);

  if (!answer) return null;

  return (
    <Card className="animate-fade-in" ref={ref}>
      <h2 className="text-base font-semibold text-text mb-4 flex items-center gap-2">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3" />
        </svg>
        Research Findings
      </h2>
      <div className={`markdown-content ${isStreaming ? 'typing-cursor' : ''}`}>
        <Markdown remarkPlugins={[remarkGfm]}>
          {answer}
        </Markdown>
      </div>
    </Card>
  );
}
