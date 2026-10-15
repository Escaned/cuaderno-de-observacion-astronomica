import { useEffect } from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { useTheme } from '../hooks/useTheme';
import { useObservatorio } from '../hooks/useObservatorio';

const navItems = [
  { to: '/', label: 'Dashboard', icon: '📊' },
  { to: '/observaciones', label: 'Observaciones', icon: '🔭' },
  { to: '/observaciones/new', label: 'Nueva', icon: '➕' },
  { to: '/admin/filtros', label: 'Filtros', icon: '🎨' },
  { to: '/admin/asociacion', label: 'Asociación', icon: '🏛️' },
];

export function Layout() {
  const { isDark, toggle } = useTheme();
  const { data: observatorio } = useObservatorio();

  const logoSrc = observatorio?.logo_path ? `/imagenes/${observatorio.logo_path}` : null;
  const nombre = observatorio?.nombre || 'Riguel';

  // Keep the browser tab icon in sync with the association logo
  useEffect(() => {
    if (!logoSrc) return;

    let link = document.querySelector<HTMLLinkElement>('link[rel="icon"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'icon';
      document.head.appendChild(link);
    }
    link.href = logoSrc;
  }, [logoSrc]);

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 p-4 flex flex-col">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          {logoSrc && (
            <img
              src={logoSrc}
              alt="Logo de la asociación"
              className="h-14 w-14 object-contain rounded-lg"
            />
          )}
          <h1 className="text-lg font-bold text-space-600 dark:text-space-400 leading-tight">{nombre}</h1>
        </div>
        <nav className="flex-1 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-space-100 dark:bg-space-900 text-space-700 dark:text-space-300'
                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`
              }
            >
              <span>{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <button
          onClick={toggle}
          className="mt-4 px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
        >
          {isDark ? '☀️ Claro' : '🌙 Oscuro'}
        </button>
      </aside>
      <main className="flex-1 p-6 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
