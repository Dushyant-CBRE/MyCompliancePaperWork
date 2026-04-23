import {
    ResponsiveContainer,
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
} from 'recharts';

interface ProcessingLineChartProps {
    data: { time: string; count: number }[];
}

export function ProcessingLineChart({ data }: ProcessingLineChartProps) {
    return (
        <div className="bg-card border border-border rounded-lg p-6">
            <h3 className="mb-4">Documents Processed (24h)</h3>
            <ResponsiveContainer width="100%" height={250}>
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="time" stroke="#9ca3af" />
                    <YAxis stroke="#9ca3af" />
                    <Tooltip />
                    <Line type="monotone" dataKey="count" stroke="#003F2D" strokeWidth={2} />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
}
