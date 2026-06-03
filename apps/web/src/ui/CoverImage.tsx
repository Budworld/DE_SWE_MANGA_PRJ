interface CoverImageProps {
  src: string | null;
  title: string;
  large?: boolean;
}

export function CoverImage({ src, title, large = false }: CoverImageProps) {
  return (
    <div className={large ? "cover cover-large" : "cover"}>
      {src ? (
        <img
          src={src}
          alt={`${title} cover`}
          loading="lazy"
          onError={(event) => {
            event.currentTarget.style.display = "none";
          }}
        />
      ) : null}
      <span className="cover-fallback">{title.slice(0, 2).toUpperCase()}</span>
    </div>
  );
}
