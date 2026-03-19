import { useState } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { BookOpen, ChevronRight } from "lucide-react";
import { motion } from "framer-motion";

interface WikiArticle {
  id: string;
  title: string;
  content?: string;
  children?: WikiArticle[];
}

const defaultArticles: WikiArticle[] = [
  {
    id: "platform",
    title: "Plataforma",
    children: [
      {
        id: "intro",
        title: "Introdução",
        content: `## Introdução

Bem-vindo à plataforma de assistente inteligente.

### Objetivo
Centralizar conhecimento interno e facilitar o acesso às informações.`,
      },
      {
        id: "features",
        title: "Funcionalidades",
        content: `## Funcionalidades

### Principais

- Chatbot inteligente
- Base de conhecimento
- Interface moderna`,
      },
    ],
  },
  {
    id: "chatbot",
    title: "Chatbot",
    children: [
      {
        id: "chatbot-guide",
        title: "Guia do Chatbot",
        content: `## Guia do Chatbot

O chatbot auxilia no dia a dia.

### Boas práticas

- Faça perguntas claras
- Forneça contexto`,
      },
      {
        id: "faq",
        title: "Perguntas Frequentes",
        content: `## FAQ

### O chatbot funciona 24h?
Sim.`,
      },
    ],
  },
  {
    id: "security",
    title: "Segurança",
    content: `## Segurança

### Medidas

- Criptografia
- Autenticação segura
- Monitoramento`,
  },
];

const renderContent = (content?: string) => {
  if (!content) return null;

  return content.split("\n").map((line, i) => {
    const trimmed = line.trim();

    if (trimmed.startsWith("## "))
      return (
        <h2 key={i} className="text-2xl font-bold mt-6 mb-4">
          {trimmed.slice(3)}
        </h2>
      );

    if (trimmed.startsWith("### "))
      return (
        <h3 key={i} className="text-lg font-semibold mt-4 mb-2">
          {trimmed.slice(4)}
        </h3>
      );

    if (trimmed.startsWith("- "))
      return (
        <li key={i} className="ml-4 mb-1">
          {trimmed.slice(2)}
        </li>
      );

    if (trimmed === "") return <br key={i} />;

    return (
      <p key={i} className="text-muted-foreground mb-2">
        {trimmed}
      </p>
    );
  });
};

const Wikis = () => {
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const findArticle = (
    articles: WikiArticle[],
    id: string
  ): WikiArticle | null => {
    for (const article of articles) {
      if (article.id === id) return article;
      if (article.children) {
        const found = findArticle(article.children, id);
        if (found) return found;
      }
    }
    return null;
  };

  const selected = selectedId
    ? findArticle(defaultArticles, selectedId)
    : null;

  const renderArticles = (articles: WikiArticle[], level = 0) => {
    return articles.map((article) => (
      <div key={article.id}>
        <button
          onClick={() => article.content && setSelectedId(article.id)}
          className={`w-full text-left flex items-center gap-2 px-3 py-2 text-sm rounded-lg transition-colors ${
            selectedId === article.id
              ? "bg-primary text-primary-foreground"
              : "hover:bg-muted"
          }`}
          style={{ paddingLeft: `${12 + level * 16}px` }}
        >
          <ChevronRight className="w-4 h-4" />
          <span>{article.title}</span>
        </button>

        {article.children && renderArticles(article.children, level + 1)}
      </div>
    ));
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)]">
      {/* Sidebar */}
      <div className="w-72 border-r bg-card flex flex-col shrink-0">
        <div className="p-4 border-b">
          <h2 className="font-bold flex items-center gap-2">
            <BookOpen className="w-5 h-5 text-accent" />
            Base de conhecimento
          </h2>
        </div>

        <ScrollArea className="flex-1">
          <div className="p-2 space-y-1">
            {renderArticles(defaultArticles)}
          </div>
        </ScrollArea>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {selected ? (
          <motion.div
            key={selected.id}
            initial={{ opacity: 0, x: 10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.25 }}
            className="max-w-3xl mx-auto p-8"
          >
            {renderContent(selected.content)}
          </motion.div>
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            <p>Selecione um tópico.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Wikis;