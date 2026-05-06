interface StatCardProps {
    label: string;
    value: string;
    change: string;
    isSelected?: boolean;
    selectedColor?: 'green' | 'yellow' | 'red' | 'blue';
    onClick?: () => void;
}

const colorMap = {
    green:  { ring: 'ring-green-400/40',  border: 'border-green-500',  text: 'text-green-600',  bg: 'bg-green-50' },
    yellow: { ring: 'ring-yellow-400/40', border: 'border-yellow-500', text: 'text-yellow-600', bg: 'bg-yellow-50' },
    red:    { ring: 'ring-red-400/40',    border: 'border-red-500',    text: 'text-red-600',    bg: 'bg-red-50' },
    blue:   { ring: 'ring-blue-400/40',   border: 'border-blue-500',   text: 'text-blue-600',   bg: 'bg-blue-50' },
};

export function StatCard({ label, value, change, isSelected, selectedColor = 'blue', onClick }: StatCardProps) {
    const colors = colorMap[selectedColor];
    return (
        <div
            onClick={onClick}
            className={`border rounded-lg p-4 transition-all ${
                onClick ? 'cursor-pointer hover:shadow-md' : ''
            } ${
                isSelected
                    ? `${colors.bg} ${colors.border} ring-2 ${colors.ring}`
                    : 'bg-card border-border hover:border-muted-foreground/40'
            }`}
        >
            <p className={`text-sm font-medium ${isSelected ? colors.text : 'text-muted-foreground'}`}>{label}</p>
            <p className={`text-3xl font-bold mt-1 ${isSelected ? colors.text : ''}`}>{value}</p>
            <p className={`text-sm mt-1 ${isSelected ? colors.text + '/80' : 'text-muted-foreground'}`}>{change}</p>
        </div>
    );
}
