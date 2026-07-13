import { Link } from "react-router-dom";
import { ChevronRight } from "lucide-react";

// Reusable breadcrumb trail. items: [{ label, to? }]
export default function Breadcrumbs({ items }) {
  return (
    <nav className="flex items-center gap-1.5 text-sm text-muted-foreground mb-4" data-testid="breadcrumbs">
      {items.map((item, i) => (
        <span key={i} className="flex items-center gap-1.5">
          {i > 0 && <ChevronRight className="h-3.5 w-3.5 opacity-50" />}
          {item.to ? (
            <Link to={item.to} className="hover:text-foreground transition-colors">
              {item.label}
            </Link>
          ) : (
            <span className="text-foreground font-medium truncate max-w-[220px] inline-block align-bottom">
              {item.label}
            </span>
          )}
        </span>
      ))}
    </nav>
  );
}
