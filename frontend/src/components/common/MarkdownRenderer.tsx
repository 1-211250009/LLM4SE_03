import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github.css';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
  return (
    <div className={className}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          // 自定义组件样式
          h1: ({ children }) => (
            <h1 style={{ 
              fontSize: '1.5rem', 
              fontWeight: 'bold', 
              margin: '16px 0 8px 0',
              color: '#1f2937',
              borderBottom: '2px solid #e5e7eb',
              paddingBottom: '8px'
            }}>
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 style={{ 
              fontSize: '1.25rem', 
              fontWeight: 'bold', 
              margin: '12px 0 6px 0',
              color: '#374151'
            }}>
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 style={{ 
              fontSize: '1.1rem', 
              fontWeight: 'bold', 
              margin: '10px 0 4px 0',
              color: '#4b5563'
            }}>
              {children}
            </h3>
          ),
          p: ({ children }) => (
            <p style={{ 
              margin: '8px 0', 
              lineHeight: '1.6',
              color: '#374151'
            }}>
              {children}
            </p>
          ),
          ul: ({ children }) => (
            <ul style={{ 
              margin: '8px 0', 
              paddingLeft: '20px',
              color: '#374151'
            }}>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol style={{ 
              margin: '8px 0', 
              paddingLeft: '20px',
              color: '#374151'
            }}>
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li style={{ 
              margin: '4px 0',
              lineHeight: '1.5'
            }}>
              {children}
            </li>
          ),
          blockquote: ({ children }) => (
            <blockquote style={{ 
              margin: '12px 0', 
              padding: '12px 16px',
              borderLeft: '4px solid #3b82f6',
              background: '#f8fafc',
              borderRadius: '0 4px 4px 0',
              color: '#475569'
            }}>
              {children}
            </blockquote>
          ),
          code: ({ children, className }) => {
            const isInline = !className;
            if (isInline) {
              return (
                <code style={{ 
                  background: '#f1f5f9',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  color: '#e11d48',
                  fontFamily: 'Monaco, Consolas, "Courier New", monospace'
                }}>
                  {children}
                </code>
              );
            }
            return <code className={className}>{children}</code>;
          },
          pre: ({ children }) => (
            <pre style={{ 
              background: '#1e293b',
              color: '#e2e8f0',
              padding: '16px',
              borderRadius: '8px',
              overflow: 'auto',
              margin: '12px 0',
              fontSize: '0.9rem',
              lineHeight: '1.5'
            }}>
              {children}
            </pre>
          ),
          table: ({ children }) => (
            <div style={{ overflowX: 'auto', margin: '12px 0' }}>
              <table style={{ 
                width: '100%',
                borderCollapse: 'collapse',
                border: '1px solid #e5e7eb',
                borderRadius: '8px',
                overflow: 'hidden'
              }}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead style={{ background: '#f9fafb' }}>
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th style={{ 
              padding: '12px 16px',
              textAlign: 'left',
              fontWeight: '600',
              color: '#374151',
              borderBottom: '1px solid #e5e7eb'
            }}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td style={{ 
              padding: '12px 16px',
              borderBottom: '1px solid #f3f4f6',
              color: '#374151'
            }}>
              {children}
            </td>
          ),
          a: ({ children, href }) => (
            <a 
              href={href} 
              target="_blank" 
              rel="noopener noreferrer"
              style={{ 
                color: '#3b82f6',
                textDecoration: 'none',
                borderBottom: '1px solid transparent',
                transition: 'border-color 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderBottomColor = '#3b82f6';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderBottomColor = 'transparent';
              }}
            >
              {children}
            </a>
          ),
          strong: ({ children }) => (
            <strong style={{ fontWeight: '600', color: '#1f2937' }}>
              {children}
            </strong>
          ),
          em: ({ children }) => (
            <em style={{ fontStyle: 'italic', color: '#6b7280' }}>
              {children}
            </em>
          ),
          hr: () => (
            <hr style={{ 
              border: 'none',
              borderTop: '1px solid #e5e7eb',
              margin: '16px 0'
            }} />
          )
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
