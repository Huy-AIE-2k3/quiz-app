import React, { forwardRef } from 'react';

export interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  readonly wrapperClassName?: string;
}

export const Table = forwardRef<HTMLTableElement, TableProps>(
  ({ className = '', wrapperClassName = '', children, ...rest }, ref) => (
    <div className={`relative w-full overflow-auto rounded-md border border-line-subtle bg-surface ${wrapperClassName}`}>
      <table ref={ref} className={`w-full text-left text-sm font-sans ${className}`} {...rest}>
        {children}
      </table>
    </div>
  )
);
Table.displayName = 'Table';

export interface TableHeaderProps extends React.HTMLAttributes<HTMLTableSectionElement> {}
export const TableHeader = forwardRef<HTMLTableSectionElement, TableHeaderProps>(
  ({ className = '', children, ...rest }, ref) => (
    <thead ref={ref} className={`bg-elevated border-b border-line-subtle ${className}`} {...rest}>
      {children}
    </thead>
  )
);
TableHeader.displayName = 'TableHeader';

export interface TableBodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {}
export const TableBody = forwardRef<HTMLTableSectionElement, TableBodyProps>(
  ({ className = '', children, ...rest }, ref) => (
    <tbody ref={ref} className={`divide-y divide-line-subtle ${className}`} {...rest}>
      {children}
    </tbody>
  )
);
TableBody.displayName = 'TableBody';

export interface TableFooterProps extends React.HTMLAttributes<HTMLTableSectionElement> {}
export const TableFooter = forwardRef<HTMLTableSectionElement, TableFooterProps>(
  ({ className = '', children, ...rest }, ref) => (
    <tfoot ref={ref} className={`border-t border-line-subtle bg-elevated font-medium ${className}`} {...rest}>
      {children}
    </tfoot>
  )
);
TableFooter.displayName = 'TableFooter';

export interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  readonly isSelected?: boolean;
}
export const TableRow = forwardRef<HTMLTableRowElement, TableRowProps>(
  ({ isSelected, className = '', children, ...rest }, ref) => (
    <tr
      ref={ref}
      className={`transition-colors hover:bg-elevated/60 ${isSelected ? 'bg-subtle-accent' : ''} ${className}`}
      {...rest}
    >
      {children}
    </tr>
  )
);
TableRow.displayName = 'TableRow';

export interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {}
export const TableHead = forwardRef<HTMLTableCellElement, TableHeadProps>(
  ({ className = '', children, ...rest }, ref) => (
    <th
      ref={ref}
      className={`h-10 px-4 text-xs font-mono font-semibold text-text-secondary uppercase tracking-wider text-left align-middle ${className}`}
      {...rest}
    >
      {children}
    </th>
  )
);
TableHead.displayName = 'TableHead';

export interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {}
export const TableCell = forwardRef<HTMLTableCellElement, TableCellProps>(
  ({ className = '', children, ...rest }, ref) => (
    <td ref={ref} className={`p-4 align-middle text-text-primary text-sm ${className}`} {...rest}>
      {children}
    </td>
  )
);
TableCell.displayName = 'TableCell';

export interface TableCaptionProps extends React.HTMLAttributes<HTMLTableCaptionElement> {}
export const TableCaption = forwardRef<HTMLTableCaptionElement, TableCaptionProps>(
  ({ className = '', children, ...rest }, ref) => (
    <caption ref={ref} className={`mt-3 text-xs text-text-muted italic ${className}`} {...rest}>
      {children}
    </caption>
  )
);
TableCaption.displayName = 'TableCaption';
