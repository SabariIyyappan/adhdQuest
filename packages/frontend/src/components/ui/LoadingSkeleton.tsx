interface LoadingSkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
}

export function LoadingSkeleton({ width = "100%", height = "20px", borderRadius = "8px" }: LoadingSkeletonProps) {
  return (
    <div
      className="animate-shimmer"
      style={{
        width: typeof width === "number" ? `${width}px` : width,
        height: typeof height === "number" ? `${height}px` : height,
        borderRadius: typeof borderRadius === "number" ? `${borderRadius}px` : borderRadius,
        display: "block",
      }}
    />
  );
}
