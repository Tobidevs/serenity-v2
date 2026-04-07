"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { AgentMode, Denomination } from "@/lib/chat-api";

const DENOMINATION_OPTIONS: Array<{ value: Denomination; label: string }> = [
  { value: "catholic", label: "Catholic" },
  { value: "orthodox", label: "Orthodox" },
  { value: "reformed", label: "Reformed" },
  { value: "anglican", label: "Anglican" },
  { value: "lutheran", label: "Lutheran" },
];

const MODE_OPTIONS: Array<{ value: AgentMode; label: string }> = [
  { value: "devotional", label: "Devotional" },
  { value: "academic", label: "Academic" },
];

type SelectOption<T extends string> = {
  value: T;
  label: string;
};

type StyledSelectProps<T extends string> = {
  value: T;
  options: Array<SelectOption<T>>;
  onChange: (value: T) => void;
  disabled: boolean;
  ariaLabel: string;
};

function StyledSelect<T extends string>({
  value,
  options,
  onChange,
  disabled,
  ariaLabel,
}: StyledSelectProps<T>) {
  const [isOpen, setIsOpen] = useState(false);
  const [highlightIndex, setHighlightIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement | null>(null);
  const triggerRef = useRef<HTMLButtonElement | null>(null);

  const selectedIndex = useMemo(
    () => options.findIndex((option) => option.value === value),
    [options, value],
  );

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    const onEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onEscape);

    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onEscape);
    };
  }, [isOpen]);

  const openMenu = () => {
    if (disabled) {
      return;
    }

    setHighlightIndex(selectedIndex >= 0 ? selectedIndex : 0);
    setIsOpen(true);
  };

  const closeMenu = () => {
    setIsOpen(false);
    setHighlightIndex(-1);
  };

  const selectOption = (option: SelectOption<T>) => {
    onChange(option.value);
    closeMenu();
    triggerRef.current?.focus();
  };

  const handleTriggerKeyDown = (
    event: React.KeyboardEvent<HTMLButtonElement>,
  ) => {
    if (disabled) {
      return;
    }

    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      openMenu();
      return;
    }

    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      if (isOpen) {
        closeMenu();
      } else {
        openMenu();
      }
    }
  };

  const handleOptionKeyDown = (
    event: React.KeyboardEvent<HTMLUListElement>,
  ) => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setHighlightIndex((previous) => {
        if (previous < 0) {
          return 0;
        }
        return (previous + 1) % options.length;
      });
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setHighlightIndex((previous) => {
        if (previous < 0) {
          return options.length - 1;
        }
        return (previous - 1 + options.length) % options.length;
      });
      return;
    }

    if (event.key === "Enter") {
      event.preventDefault();
      if (highlightIndex >= 0) {
        selectOption(options[highlightIndex]);
      }
      return;
    }

    if (event.key === "Escape") {
      event.preventDefault();
      closeMenu();
      triggerRef.current?.focus();
    }
  };

  const selectedLabel =
    options.find((option) => option.value === value)?.label ?? "";

  return (
    <div className="composer-select-wrap" ref={rootRef}>
      <button
        ref={triggerRef}
        type="button"
        className="composer-select"
        disabled={disabled}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={ariaLabel}
        onClick={() => {
          if (isOpen) {
            closeMenu();
          } else {
            openMenu();
          }
        }}
        onKeyDown={handleTriggerKeyDown}
      >
        <span className="composer-select-label">{selectedLabel}</span>
      </button>

      <svg
        aria-hidden="true"
        viewBox="0 0 12 12"
        className={`composer-select-icon ${isOpen ? "is-open" : ""}`}
      >
        <path
          d="M2 8 L6 4 L10 8"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>

      {isOpen && !disabled ? (
        <ul
          className="composer-dropdown absolute bottom-[calc(100%+0.45rem)] left-0 z-30 min-w-full"
          role="listbox"
          tabIndex={-1}
          aria-label={ariaLabel}
          onKeyDown={handleOptionKeyDown}
        >
          {options.map((option, index) => {
            const isSelected = option.value === value;
            const isHighlighted = highlightIndex === index;

            return (
              <li key={option.value} role="presentation">
                <button
                  type="button"
                  role="option"
                  aria-selected={isSelected}
                  className={`composer-dropdown-option w-full ${isSelected ? "is-selected" : ""} ${
                    isHighlighted ? "is-highlighted" : ""
                  }`}
                  onMouseEnter={() => setHighlightIndex(index)}
                  onClick={() => selectOption(option)}
                >
                  <span>{option.label}</span>
                  {isSelected ? (
                    <span
                      className="composer-dropdown-check"
                      aria-hidden="true"
                    >
                      <svg
                        viewBox="0 0 16 16"
                        className="h-3.5 w-3.5"
                        fill="none"
                      >
                        <path
                          d="M3.2 8.2l3.1 3.2 6.2-6.6"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                    </span>
                  ) : null}
                </button>
              </li>
            );
          })}
        </ul>
      ) : null}
    </div>
  );
}

type ChatBoxProps = {
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  denomination: Denomination;
  onDenominationChange: (value: Denomination) => void;
  mode: AgentMode;
  onModeChange: (value: AgentMode) => void;
  pending: boolean;
  errorMessage: string | null;
};

export function ChatBox({
  input,
  onInputChange,
  onSend,
  denomination,
  onDenominationChange,
  mode,
  onModeChange,
  pending,
  errorMessage,
}: ChatBoxProps) {
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const canSend = input.trim().length > 0 && !pending;

  const resizeTextarea = () => {
    if (!textareaRef.current) {
      return;
    }

    textareaRef.current.style.height = "0px";
    textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
  };

  useEffect(() => {
    resizeTextarea();
  }, [input]);

  return (
    <div className="chat-composer-panel ">
      <div>
        <textarea
          ref={textareaRef}
          rows={1}
          className="chat-composer-input"
          value={input}
          placeholder="Type in your message..."
          onChange={(event) => {
            onInputChange(event.target.value);
            resizeTextarea();
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              if (canSend) {
                onSend();
              }
            }
          }}
          disabled={pending}
        />

        <div className="composer-controls">
          <div className="composer-selects">
            <StyledSelect
              value={denomination}
              options={DENOMINATION_OPTIONS}
              onChange={onDenominationChange}
              disabled={pending}
              ariaLabel="Denomination"
            />

            <StyledSelect
              value={mode}
              options={MODE_OPTIONS}
              onChange={onModeChange}
              disabled={pending}
              ariaLabel="Mode"
            />
          </div>

          <button
            type="button"
            aria-label={pending ? "Sending" : "Send message"}
            className="composer-send"
            onClick={onSend}
            disabled={!canSend}
          >
            <svg
              viewBox="0 0 24 24"
              className="h-[1.08rem] w-[1.08rem]"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M12 18V6"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
              />
              <path
                d="M6.8 11.2L12 6l5.2 5.2"
                stroke="currentColor"
                strokeWidth="2.4"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        {errorMessage ? <p className="chat-error">{errorMessage}</p> : null}
      </div>
    </div>
  );
}
