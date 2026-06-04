export function LoadingBlock() {
  return <div className="state-block">Loading...</div>;
}

export function ErrorBlock({ message }: { message: string }) {
  return <div className="state-block state-error">{message}</div>;
}
