import { Card, CardContent } from "@/components/ui/card";
import { Bot, BookOpen, Shield, Zap } from "lucide-react";
import { motion } from "framer-motion";

const features = [
  {
    icon: Bot,
    title: "Assistente Inteligente",
    description: "Chatbot alimentado por IA para responder perguntas e auxiliar em tarefas do dia a dia.",
  },
  {
    icon: BookOpen,
    title: "Base de Conhecimento",
    description: "Wiki integrada com artigos, guias e documentação para consulta rápida.",
  },
  {
    icon: Shield,
    title: "Segurança",
    description: "Dados protegidos com criptografia e conformidade com as melhores práticas de segurança.",
  },
  {
    icon: Zap,
    title: "Alta Performance",
    description: "Interface rápida e responsiva, acessível de qualquer dispositivo.",
  },
];

const About = () => {
  return (
    <div className="h-[calc(100vh-3.5rem)] overflow-auto">
      <div className="max-w-3xl mx-auto p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <h1 className="text-3xl font-display font-bold text-foreground mb-2">
            Sobre a plataforma
          </h1>
          <p className="text-muted-foreground mb-8 text-lg">
            Uma plataforma moderna de assistente inteligente para empresas.
          </p>

          <div className="space-y-4 mb-10">
            <p className="text-foreground leading-relaxed">
              Esta plataforma foi desenvolvida para centralizar o acesso a informações e fornecer suporte inteligente por meio de um chatbot baseado em inteligência artificial. Nosso objetivo é aumentar a produtividade e facilitar o acesso ao conhecimento organizacional.
            </p>
            <p className="text-foreground leading-relaxed">
              A ferramenta combina um assistente virtual com uma base de conhecimento completa, permitindo que os usuários encontrem respostas rapidamente e de forma autônoma.
            </p>
          </div>

          <h2 className="text-xl font-display font-bold text-foreground mb-4">
            Principais recursos
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-10">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
              >
                <Card className="border bg-card shadow-sm hover:shadow-md transition-shadow">
                  <CardContent className="p-5">
                    <div className="w-10 h-10 rounded-xl bg-primary/10 flex items-center justify-center mb-3">
                      <feature.icon className="w-5 h-5 text-primary" />
                    </div>
                    <h3 className="font-display font-semibold text-foreground mb-1">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          <h2 className="text-xl font-display font-bold text-foreground mb-4">
            Como usar
          </h2>
          <ol className="list-decimal list-inside space-y-2 text-foreground mb-8">
            <li>Faça login com suas credenciais</li>
            <li>Acesse o <strong>Chatbot</strong> para fazer perguntas ao assistente</li>
            <li>Consulte as <strong>Wikis</strong> para informações detalhadas</li>
            <li>Explore os recursos da plataforma conforme sua necessidade</li>
          </ol>
        </motion.div>
      </div>
    </div>
  );
};

export default About;
