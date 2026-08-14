/**
 * Lightweight, dependency-free markdown renderer.
 * Supports: headings, bold, italic, inline code, code blocks,
 * unordered/ordered lists, blockquotes, links, and paragraphs.
 * Returns an array of React element nodes.
 */
import { createElement, type ReactNode } from 'react';

export function renderMarkdown(md: string): ReactNode[] {
  const lines = md.split('\n');
  const nodes: ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.trim().startsWith('```')) {
      const lang = line.trim().slice(3);
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].trim().startsWith('```')) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      nodes.push(
        createElement('pre', { key: key++ },
          createElement('code', { className: lang ? `language-${lang}` : undefined }, codeLines.join('\n')),
        ),
      );
      continue;
    }

    // Headings
    const h = line.match(/^(#{1,3})\s+(.*)$/);
    if (h) {
      const level = h[1].length;
      nodes.push(createElement(`h${level}`, { key: key++ }, inline(h[2])));
      i++;
      continue;
    }

    // Blockquote
    if (line.trim().startsWith('>')) {
      const quoteLines: string[] = [];
      while (i < lines.length && lines[i].trim().startsWith('>')) {
        quoteLines.push(lines[i].trim().replace(/^>\s?/, ''));
        i++;
      }
      nodes.push(createElement('blockquote', { key: key++ }, inline(quoteLines.join(' '))));
      continue;
    }

    // Unordered list
    if (/^\s*[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*[-*]\s+/, ''));
        i++;
      }
      nodes.push(
        createElement('ul', { key: key++ }, items.map((t, idx) =>
          createElement('li', { key: idx }, inline(t)),
        )),
      );
      continue;
    }

    // Ordered list
    if (/^\s*\d+\.\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\s*\d+\.\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\s*\d+\.\s+/, ''));
        i++;
      }
      nodes.push(
        createElement('ol', { key: key++ }, items.map((t, idx) =>
          createElement('li', { key: idx }, inline(t)),
        )),
      );
      continue;
    }

    // Empty line
    if (line.trim() === '') {
      i++;
      continue;
    }

    // Paragraph (gather consecutive non-empty, non-special lines)
    const paraLines: string[] = [];
    while (
      i < lines.length &&
      lines[i].trim() !== '' &&
      !lines[i].trim().startsWith('```') &&
      !/^(#{1,3})\s+/.test(lines[i]) &&
      !lines[i].trim().startsWith('>') &&
      !/^\s*[-*]\s+/.test(lines[i]) &&
      !/^\s*\d+\.\s+/.test(lines[i])
    ) {
      paraLines.push(lines[i]);
      i++;
    }
    nodes.push(createElement('p', { key: key++ }, inline(paraLines.join(' '))));
  }

  return nodes;
}

function inline(text: string): ReactNode[] {
  const tokens: ReactNode[] = [];
  let remaining = text;
  let key = 0;

  // Order matters: code first, then bold, then italic, then links
  const patterns: { regex: RegExp; render: (m: RegExpExecArray) => ReactNode }[] = [
    {
      regex: /`([^`]+)`/,
      render: (m) => createElement('code', { key: key++ }, m[1]),
    },
    {
      regex: /\*\*([^*]+)\*\*/,
      render: (m) => createElement('strong', { key: key++ }, inline(m[1])),
    },
    {
      regex: /\*([^*]+)\*/,
      render: (m) => createElement('em', { key: key++ }, inline(m[1])),
    },
    {
      regex: /\[([^\]]+)\]\(([^)]+)\)/,
      render: (m) => createElement('a', { key: key++, href: m[2], target: '_blank', rel: 'noopener noreferrer' }, m[1]),
    },
  ];

  while (remaining.length > 0) {
    let earliest = -1;
    let matched: { index: number; node: ReactNode; length: number } | null = null;

    for (const p of patterns) {
      const m = p.regex.exec(remaining);
      if (m && (earliest === -1 || m.index < earliest)) {
        earliest = m.index;
        matched = { index: m.index, node: p.render(m), length: m[0].length };
      }
    }

    if (matched && matched.index >= 0) {
      if (matched.index > 0) {
        tokens.push(remaining.slice(0, matched.index));
      }
      tokens.push(matched.node);
      remaining = remaining.slice(matched.index + matched.length);
    } else {
      tokens.push(remaining);
      break;
    }
  }

  return tokens;
}
