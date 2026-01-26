import { ExternalLink, MapPin, Calendar, Clock } from 'lucide-react';

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
const sourceColors: Record<string, { gradient: string; glow: string }> = {
  Luma: { gradient: 'from-violet-500 to-purple-600', glow: 'violet' },
  Eventbrite: { gradient: 'from-orange-500 to-red-500', glow: 'orange' },
  Meetup: { gradient: 'from-red-500 to-pink-500', glow: 'red' },
  default: { gradient: 'from-cyan-500 to-blue-500', glow: 'cyan' },
};

function getSourceColors(source: string) {
  return sourceColors[source] || sourceColors.default;
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
  const colors = getSourceColors(event.source);

  const handleClick = () => {
    window.open(event.url, '_blank', 'noopener,noreferrer');
  };

  return (
    <div
      onClick={handleClick}
      className="event-card-glass rounded-xl p-4 cursor-pointer group"
    >
      {/* Header with title and source badge */}
      <div className="flex items-start justify-between gap-3">
        <h4 className="font-semibold text-white group-hover:text-cyan-300 transition-colors line-clamp-2 flex-1">
          {event.title}
        </h4>
        <span
          className={`bg-gradient-to-r ${colors.gradient} text-white text-xs font-medium px-2.5 py-1 rounded-full whitespace-nowrap`}
        >
          {event.source}
        </span>
      </div>

      {/* Event details */}
      <div className="mt-3 space-y-2 text-sm">
        {/* Date */}
        <div className="flex items-center gap-2 text-white/60">
          <Calendar className="w-4 h-4 text-violet-400 flex-shrink-0" />
          <span>{formatDate(event.date)}</span>
        </div>

        {/* Time */}
        {event.time && (
          <div className="flex items-center gap-2 text-white/60">
            <Clock className="w-4 h-4 text-cyan-400 flex-shrink-0" />
            <span>{event.time}</span>
          </div>
        )}

        {/* Location */}
        {event.location && (
          <div className="flex items-center gap-2 text-white/60">
            <MapPin className="w-4 h-4 text-pink-400 flex-shrink-0" />
            <span className="line-clamp-1">{event.location}</span>
          </div>
        )}
      </div>

      {/* Description preview */}
      {event.description && (
        <p className="mt-3 text-sm text-white/40 line-clamp-2">{event.description}</p>
      )}

      {/* Tags */}
      {event.tags && event.tags.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1.5">
          {event.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="text-xs bg-white/5 text-white/50 px-2 py-0.5 rounded-md border border-white/10"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Link indicator */}
      <div className="mt-3 flex items-center text-xs text-cyan-400 group-hover:text-cyan-300 transition-colors">
        <ExternalLink className="w-3 h-3 mr-1.5" />
        <span>View event</span>
      </div>
    </div>
  );
}
