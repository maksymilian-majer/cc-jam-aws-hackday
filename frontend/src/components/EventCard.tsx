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

// Color scheme for different event sources
const sourceColors: Record<string, { bg: string; text: string; border: string }> = {
  Luma: { bg: 'bg-purple-100', text: 'text-purple-800', border: 'border-purple-300' },
  Eventbrite: { bg: 'bg-orange-100', text: 'text-orange-800', border: 'border-orange-300' },
  Meetup: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-300' },
  default: { bg: 'bg-blue-100', text: 'text-blue-800', border: 'border-blue-300' },
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
      year: 'numeric',
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
      className={`border ${colors.border} rounded-lg p-3 my-2 bg-white hover:shadow-md transition-shadow cursor-pointer group`}
    >
      {/* Header with title and source badge */}
      <div className="flex items-start justify-between gap-2">
        <h4 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-2 flex-1">
          {event.title}
        </h4>
        <span
          className={`${colors.bg} ${colors.text} text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap`}
        >
          {event.source}
        </span>
      </div>

      {/* Event details */}
      <div className="mt-2 space-y-1 text-sm text-gray-600">
        {/* Date */}
        <div className="flex items-center gap-1.5">
          <Calendar className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <span>{formatDate(event.date)}</span>
        </div>

        {/* Time */}
        {event.time && (
          <div className="flex items-center gap-1.5">
            <Clock className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <span>{event.time}</span>
          </div>
        )}

        {/* Location */}
        {event.location && (
          <div className="flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0" />
            <span className="line-clamp-1">{event.location}</span>
          </div>
        )}
      </div>

      {/* Description preview */}
      {event.description && (
        <p className="mt-2 text-sm text-gray-500 line-clamp-2">{event.description}</p>
      )}

      {/* Tags */}
      {event.tags && event.tags.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {event.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* Link indicator */}
      <div className="mt-2 flex items-center text-xs text-indigo-600 group-hover:text-indigo-800">
        <ExternalLink className="w-3 h-3 mr-1" />
        <span>View event</span>
      </div>
    </div>
  );
}
