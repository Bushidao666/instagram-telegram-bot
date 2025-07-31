import { toast } from 'sonner'

export { toast }

export const useToast = () => {
  return {
    toast: (props: {
      title?: string
      description?: string
      variant?: 'default' | 'destructive'
    }) => {
      const { title, description, variant } = props
      
      if (variant === 'destructive') {
        toast.error(title || 'Error', {
          description: description,
        })
      } else {
        toast.success(title || 'Success', {
          description: description,
        })
      }
    }
  }
}