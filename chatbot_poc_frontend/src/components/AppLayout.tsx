import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
  useSidebar,
} from "@/components/ui/sidebar";
import { NavLink } from "@/components/NavLink";
import { Bot, BookOpen, Info, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { title: "Chatbot", url: "/chatbot", icon: Bot },
  { title: "Wikis", url: "/wikis", icon: BookOpen },
  { title: "Sobre", url: "/sobre", icon: Info },
];

function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { logout, userEmail } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <Sidebar collapsible="icon" className="border-r-0">
      <SidebarContent className="flex flex-col justify-between h-full">
        <div>
          <div className="p-4 flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-sidebar-primary flex items-center justify-center shrink-0">
              <Bot className="w-5 h-5 text-sidebar-primary-foreground" />
            </div>
            {!collapsed && (
              <span className="font-display font-bold text-lg text-sidebar-foreground">
                AI Chat
              </span>
            )}
          </div>
          <SidebarGroup>
            <SidebarGroupContent>
              <SidebarMenu>
                {navItems.map((item) => (
                  <SidebarMenuItem key={item.title}>
                    <SidebarMenuButton asChild>
                      <NavLink
                        to={item.url}
                        end
                        className="hover:bg-sidebar-accent/50 text-sidebar-foreground"
                        activeClassName="bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                      >
                        <item.icon className="mr-2 h-4 w-4" />
                        {!collapsed && <span>{item.title}</span>}
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </div>

        <div className="p-4 space-y-3">
          {!collapsed && userEmail && (
            <p className="text-xs text-sidebar-foreground/60 truncate">{userEmail}</p>
          )}
          <Button
            variant="ghost"
            className="w-full justify-start text-sidebar-foreground/80 hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
            onClick={handleLogout}
          >
            <LogOut className="mr-2 h-4 w-4" />
            {!collapsed && "Sair"}
          </Button>
        </div>
      </SidebarContent>
    </Sidebar>
  );
}

const AppLayout = () => {
  return (
    <SidebarProvider>
      <div className="min-h-screen flex w-full">
        <AppSidebar />
        <div className="flex-1 flex flex-col min-w-0">
          <header className="h-14 flex items-center border-b bg-card px-4">
            <SidebarTrigger className="text-foreground" />
          </header>
          <main className="flex-1 overflow-hidden">
            <Outlet />
          </main>
        </div>
      </div>
    </SidebarProvider>
  );
};

export default AppLayout;
