import React from 'react';
import { Box } from '@mui/material';
import Markdown from 'react-markdown';

interface MarkdownRendererProps {
    content: string;
}

export const MarkdownRenderer = ({ content }: MarkdownRendererProps) => {
    return (
        <Box
            sx={{
                '& h1, & h2, & h3, & h4, & h5, & h6': {
                    mt: 2,
                    mb: 1,
                    fontFamily: 'inherit',
                },
                '& h1': { fontSize: '2rem' },
                '& h2': { fontSize: '1.5rem' },
                '& h3': { fontSize: '1.25rem' },
                '& h4': { fontSize: '1.125rem' },
                '& h5': { fontSize: '1rem' },
                '& h6': { fontSize: '0.875rem' },
                '& p': {
                    mb: 1.5,
                    lineHeight: 1.6,
                },
                '& ul, & ol': {
                    pl: 3,
                    mb: 1.5,
                },
                '& li': {
                    mb: 0.5,
                },
                '& code': {
                    fontFamily: 'monospace',
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    padding: '2px 4px',
                    borderRadius: '3px',
                    fontSize: '0.875em',
                },
                '& pre': {
                    backgroundColor: 'rgba(0, 0, 0, 0.04)',
                    padding: 2,
                    borderRadius: 1,
                    overflow: 'auto',
                    mb: 1.5,
                    '& code': {
                        backgroundColor: 'transparent',
                        padding: 0,
                    },
                },
                '& blockquote': {
                    borderLeft: '4px solid',
                    borderColor: 'divider',
                    pl: 2,
                    ml: 0,
                    fontStyle: 'italic',
                    color: 'text.secondary',
                },
                '& a': {
                    color: 'primary.main',
                    textDecoration: 'none',
                    '&:hover': {
                        textDecoration: 'underline',
                    },
                },
                '& table': {
                    borderCollapse: 'collapse',
                    width: '100%',
                    mb: 1.5,
                },
                '& th, & td': {
                    border: '1px solid',
                    borderColor: 'divider',
                    padding: 1,
                    textAlign: 'left',
                },
                '& th': {
                    backgroundColor: 'grey.50',
                    fontWeight: 600,
                },
                '& hr': {
                    border: 'none',
                    borderBottom: '1px solid',
                    borderColor: 'divider',
                    my: 2,
                },
            }}
        >
            <Markdown>{content}</Markdown>
        </Box>
    );
};
