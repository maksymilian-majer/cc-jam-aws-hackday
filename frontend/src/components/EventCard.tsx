import { ExternalLink, MapPin, Calendar, Clock } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export interface EventData {
  id: string;
  title: string;
  description?: string | null;
  date: string;
  time?: string | null;
  location?: string | null;
  url: string;
  source: string;
  tags?: string[];
}

// Color scheme for different event sources - glassmorphism style
const sourceColorsGlass: Record<string, { gradient: string; glow: string }> = {
  Luma: { gradient: 'from-violet-500 to-purple-600', glow: 'violet' },
  Eventbrite: { gradient: 'from-orange-500 to-red-500', glow: 'orange' },
  Meetup: { gradient: 'from-red-500 to-pink-500', glow: 'red' },
  default: { gradient: 'from-cyan-500 to-blue-500', glow: 'cyan' },
};

function getSourceColorsGlass(source: string) {
  return sourceColorsGlass[source] || sourceColorsGlass.default;
}

function formatDate(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

interface EventCardProps {
  event: EventData;
}

export default function EventCard({ event }: EventCardProps) {
  const { theme } = useTheme();
  const isBrutalist = theme === 'brutalist';
  const colorsGlass = getSourceColorsGlass(event.source);

  const handleClick = () => {
    window.open(event.url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div
      onClick={handleClick}
      className={`p-4 cursor-pointer group ${
        isBrutalist
          ? 'theme-event-card'
          : 'theme-event-card rounded-xl'
      }`}
    >
      {/* Header with title and source badge */}
      <div className="flex items-start justify-between gap-3">
        <h4 className={`font-semibold line-clamp-2 flex-1 transition-colors ${
          isBrutalist
            ? 'text-black uppercase tracking-wide group-hover:text-red-600'
            : 'text-white group-hover:text-cyan-300'
        }`}>
          {event.title}
        </h4>
        <span
          className={`text-xs font-medium px-2.5 py-1 whitespace-nowrap ${
            isBrutalist
              ? 'bg-black text-yellow-400 uppercase tracking-wide'
              : `bg-gradient-to-r ${colorsGlass.gradient} text-white rounded-full`
          }`}
        >
          {event.source}
        </span>
      </div>

      {/* Event details */}
      <div className="mt-3 space-y-2 text-sm">
        {/* Date */}
        <div className={`flex items-center gap-2 ${
          isBrutalist ? 'text-black/70' : 'text-white/60'
        }`}>
          <Calendar className={`w-4 h-4 flex-shrink-0 ${
            isBrutalist ? 'text-black' : 'text-violet-400'
          }`} />
          <span>{formatDate(event.date)}</span>
        </div>

        {/* Time */}
        {event.time && (
          <div className={`flex items-center gap-2 ${
            isBrutalist ? 'text-black/70' : 'text-white/60'
          }`}>
            <Clock className={`w-4 h-4 flex-shrink-0 ${
              isBrutalist ? 'text-black' : 'text-cyan-400'
            }`} />
            <span>{event.time}</span>
          </div>
        )}

        {/* Location */}
        {event.location && (
          <div className={`flex items-center gap-2 ${
            isBrutalist ? 'text-black/70' : 'text-white/60'
          }`}>
            <MapPin className={`w-4 h-4 flex-shrink-0 ${
              isBrutalist ? 'text-black' : 'text-pink-400'
            }`} />
            <span className="line-clamp-1">{event.location}</span>
          </div>
        )}
      </div>

      {/* Description preview */}
      {event.description && (
        <p className={`mt-3 text-sm line-clamp-2 ${
          isBrutalist ? 'text-black/50' : 'text-white/40'
        }`}>{event.description}</p>
      )}

      {/* Tags */}
      {event.tags && event.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {event.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className={`text-xs px-2 py-0.5 ${
                isBrutalist
                  ? 'bg-yellow-400 text-black border-2 border-black uppercase tracking-wide'
                  : 'bg-white/5 text-white/50 rounded-md border border-white/10'
              }`}
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Link indicator */}
      <div className={`mt-3 flex items-center text-xs transition-colors ${
        isBrutalist
          ? 'text-red-600 group-hover:text-red-700 uppercase tracking-wide font-bold'
          : 'text-cyan-400 group-hover:text-cyan-300'
      }`}>
        <ExternalLink className="w-3 h-3 mr-1.5" />
        <span>{isBrutalist ? 'VIEW EVENT →' : 'View event'}</span>
      </div>
    </div>
  );
}
